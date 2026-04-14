from flask import Flask, request, jsonify
import barcode
from barcode.writer import ImageWriter
import base64
import os
import io
import time
import json
import re
import requests as http_requests

app = Flask(__name__)

COTES_EMAIL    = os.environ.get('COTES_EMAIL', '')
COTES_PASSWORD = os.environ.get('COTES_PASSWORD', '')
TWOCAPTCHA_KEY = os.environ.get('TWOCAPTCHA_KEY', '')

LOGIN_URL  = 'https://zonereservee.coteetsport.ma'
BETTING_URL = 'https://www.coteetsport.ma/cote-sport'

# reCAPTCHA site key found on zonereservee.coteetsport.ma
RECAPTCHA_SITE_KEY = '6LcI_T8UAAAAAJ8sMbyTFbsKHDDGDQpVLLgT73HS'

# ─── Barcode generation ───────────────────────────────────────────────────────

def generate_barcode_image(code):
    CODE128 = barcode.get_barcode_class('code128')
    buffer = io.BytesIO()
    writer = ImageWriter()
    writer.set_options({
        'module_width': 10, 'module_height': 80,
        'font_size': 18, 'text_distance': 5,
        'background': 'white', 'foreground': 'black',
        'write_text': True, 'quiet_zone': 6.5, 'dpi': 300
    })
    code_obj = CODE128(str(code), writer=writer)
    code_obj.write(buffer)
    buffer.seek(0)
    return 'data:image/png;base64,' + base64.b64encode(buffer.read()).decode('utf-8')

# ─── 2captcha solver ──────────────────────────────────────────────────────────

def solve_recaptcha(page_url, site_key):
    """Submit captcha to 2captcha and wait for the token."""
    if not TWOCAPTCHA_KEY:
        raise Exception("TWOCAPTCHA_KEY not set")

    print("Submitting reCAPTCHA to 2captcha...")
    submit = http_requests.post('http://2captcha.com/in.php', data={
        'key': TWOCAPTCHA_KEY,
        'method': 'userrecaptcha',
        'googlekey': site_key,
        'pageurl': page_url,
        'json': 1
    })
    result = submit.json()
    if result.get('status') != 1:
        raise Exception(f"2captcha submit error: {result}")

    captcha_id = result['request']
    print(f"2captcha job ID: {captcha_id} — waiting for solution...")

    # Poll every 5 seconds, up to 2 minutes
    for attempt in range(24):
        time.sleep(5)
        poll = http_requests.get('http://2captcha.com/res.php', params={
            'key': TWOCAPTCHA_KEY,
            'action': 'get',
            'id': captcha_id,
            'json': 1
        })
        poll_result = poll.json()
        if poll_result.get('status') == 1:
            token = poll_result['request']
            print(f"reCAPTCHA token received (attempt {attempt+1})")
            return token
        elif poll_result.get('request') != 'CAPCHA_NOT_READY':
            raise Exception(f"2captcha poll error: {poll_result}")

    raise Exception("2captcha timeout: no token after 2 minutes")

# ─── Playwright bot ───────────────────────────────────────────────────────────

def place_ticket_and_get_code(matches, stake):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        # ── Step 1: Open login page ──
        page.goto(LOGIN_URL, timeout=30000)
        time.sleep(3)

        # ── Step 2: Fill email + password ──
        page.fill('input[type="email"], input[name="email"]', COTES_EMAIL)
        page.fill('input[type="password"]', COTES_PASSWORD)
        print("Credentials filled")

        # ── Step 3: Solve reCAPTCHA with 2captcha ──
        token = solve_recaptcha(LOGIN_URL, RECAPTCHA_SITE_KEY)

        # Inject token into the hidden textarea that reCAPTCHA uses
        page.evaluate(f"""
            document.getElementById('g-recaptcha-response').innerHTML = '{token}';
            if (typeof ___grecaptcha_cfg !== 'undefined') {{
                Object.entries(___grecaptcha_cfg.clients).forEach(([key, client]) => {{
                    if (client && client.l && typeof client.l.callback === 'function') {{
                        client.l.callback('{token}');
                    }}
                }});
            }}
        """)
        time.sleep(1)

        # ── Step 4: Submit login form ──
        page.click('button[type="submit"], button:has-text("Se connecter")')
        time.sleep(5)
        print("Login submitted")

        # ── Step 5: Verify login ──
        content = page.content()
        if 'Se connecter' in content and 'Mon compte' not in content:
            browser.close()
            raise Exception("Login failed — check credentials or reCAPTCHA site key")
        print("Login successful!")

        # ── Step 6: Navigate to betting page ──
        page.goto(BETTING_URL, timeout=30000)
        time.sleep(3)

        # ── Step 7: Add selections to betslip ──
        for match_data in matches:
            match_text = match_data.get('match', '')
            prono      = match_data.get('prono', '')
            print(f"Selecting: {match_text} → {prono}")
            # The site loads matches dynamically; we click directly on odds buttons
            # by matching text content of the match rows
            try:
                page.wait_for_load_state('networkidle', timeout=10000)
                # Find match row by team name
                teams = match_text.split(' vs ')
                if teams:
                    row = page.locator(f'text="{teams[0].strip()}"').first
                    if row.is_visible(timeout=3000):
                        # Navigate to match page and select the prono
                        row.click()
                        time.sleep(2)
            except Exception as e:
                print(f"Selection error for {match_text}: {e}")

        # ── Step 8: Set stake ──
        time.sleep(2)
        for sel in ['input[placeholder*="Mise"]', 'input[placeholder*="mise"]',
                    '[class*="stake"] input', '[class*="betslip"] input[type="number"]']:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.triple_click()
                    el.fill(str(stake))
                    print(f"Stake {stake} MAD set")
                    break
            except:
                pass

        # ── Step 9: Submit ticket ──
        reservation_code = None
        for sel in ['button:has-text("Valider le coupon")', 'button:has-text("Valider")',
                    'button:has-text("Jouer")', 'button:has-text("Confirmer")',
                    '[class*="submit-bet"]', '[class*="place-bet"]']:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print(f"Ticket submitted via: {sel}")
                    time.sleep(6)
                    break
            except:
                pass

        # ── Step 10: Extract reservation code ──
        page_text = page.inner_text('body')
        page.screenshot(path='/tmp/confirmation.png')

        patterns = [
            r'[Rr][eé]servations*[:#]?s*([A-Z0-9-]{6,20})',
            r'[Tt]ickets*[:#]?s*([A-Z0-9-]{6,20})',
            r'[Cc]oupons*[:#]?s*([A-Z0-9-]{6,20})',
            r'[Cc]odes*[:#]?s*([A-Z0-9-]{6,20})',
            r'N[°o.]s*([0-9]{6,15})',
            r'([0-9]{8,15})',
        ]
        for pattern in patterns:
            m = re.search(pattern, page_text)
            if m:
                reservation_code = m.group(1).strip()
                print(f"Reservation code: {reservation_code}")
                break

        browser.close()
        return reservation_code

# ─── Flask routes ─────────────────────────────────────────────────────────────

@app.route('/generate', methods=['POST'])
def generate():
    data      = request.json
    stake     = data.get('stake', 10)
    matches   = data.get('matches', [])

    reservation_code = place_ticket_and_get_code(matches, stake)

    if not reservation_code:
        return jsonify({
            'status': 'error',
            'message': 'Could not extract reservation code from confirmation page'
        }), 400

    return jsonify({
        'status': 'success',
        'barcode_url': generate_barcode_image(reservation_code),
        'reservation_code': reservation_code
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
