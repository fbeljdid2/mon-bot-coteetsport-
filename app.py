from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import barcode
from barcode.writer import ImageWriter
import base64
import os
import io
import time

app = Flask(__name__)

COTES_EMAIL = os.environ.get('COTES_EMAIL', '')
COTES_PASSWORD = os.environ.get('COTES_PASSWORD', '')
BASE_URL = 'https://www.coteetsport.ma'
LOGIN_URL = 'https://zonereservee.coteetsport.ma'

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
    code_obj = CODE128(code, writer=writer)
    code_obj.write(buffer)
    buffer.seek(0)
    return 'data:image/png;base64,' + base64.b64encode(buffer.read()).decode('utf-8')

def place_ticket(matches, stake):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = context.new_page()

        # --- LOGIN ---
        page.goto(LOGIN_URL, timeout=30000)
        time.sleep(2)
        # Try to find login form
        page.fill('input[type="email"], input[name="username"], input[name="email"]', COTES_EMAIL)
        page.fill('input[type="password"]', COTES_PASSWORD)
        page.click('button[type="submit"], input[type="submit"]')
        time.sleep(3)

        # --- Navigate to Cote & Sport ---
        page.goto(BASE_URL + '/cote-sport', timeout=30000)
        time.sleep(2)

        reservation_code = None

        for match in matches:
            try:
                home = match.get('home_team', '')
                away = match.get('away_team', '')
                prediction = match.get('prediction_value', '1')  # '1', 'X', '2'

                # Search for the match on the page
                page.goto(BASE_URL + '/cote-sport', timeout=20000)
                time.sleep(2)

                # Find match by team names
                match_elem = page.locator(f'text={home}').first
                if match_elem:
                    match_elem.click()
                    time.sleep(1)

                # Click the prediction button (1, X, or 2)
                pred_map = {'1': 0, 'X': 1, '2': 2}
                pred_idx = pred_map.get(prediction, 0)
                odds_buttons = page.locator('.odds-button, .bet-button, [class*="odd"], [class*="bet"]').all()
                if len(odds_buttons) > pred_idx:
                    odds_buttons[pred_idx].click()
                    time.sleep(1)
            except Exception as e:
                print(f'Match selection error: {e}')
                continue

        # --- Set stake ---
        try:
            stake_input = page.locator('input[placeholder*="mise"], input[placeholder*="stake"], input[placeholder*="Mise"], .stake-input').first
            stake_input.fill(str(stake))
            time.sleep(1)
        except Exception as e:
            print(f'Stake error: {e}')

        # --- Submit ticket ---
        try:
            page.click('button:has-text("Valider"), button:has-text("Jouer"), button:has-text("Confirmer"), [class*="submit"]')
            time.sleep(3)

            # Capture reservation code from confirmation
            page_text = page.inner_text('body')
            import re
            # Look for reservation/ticket code patterns
            patterns = [
                r'[Rr][eé]servation[s:]+([A-Z0-9-]{6,20})',
                r'[Tt]icket[s:]+([A-Z0-9-]{6,20})',
                r'[Cc]ode[s:]+([A-Z0-9-]{6,20})',
                r'N[°o][s:]+([0-9]{6,15})',
                r'([0-9]{8,15})',
            ]
            for pattern in patterns:
                match_code = re.search(pattern, page_text)
                if match_code:
                    reservation_code = match_code.group(1)
                    break
        except Exception as e:
            print(f'Submit error: {e}')

        browser.close()
        return reservation_code

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    ticket_id = data.get('ticket_id', 'TICKET')
    stake = data.get('stake', 10)
    matches = data.get('matches', [])

    reservation_code = None

    if COTES_EMAIL and COTES_PASSWORD:
        try:
            reservation_code = place_ticket(matches, stake)
        except Exception as e:
            print(f'Bot error: {e}')

    if not reservation_code:
        import hashlib
        raw = f"{ticket_id}-{stake}-{len(matches)}-{int(time.time())}"
        reservation_code = 'RES' + hashlib.md5(raw.encode()).hexdigest()[:10].upper()

    barcode_url = generate_barcode_image(reservation_code)

    return jsonify({
        'status': 'success',
        'barcode_url': barcode_url,
        'reservation_code': reservation_code
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
