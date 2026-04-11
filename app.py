 Bot coteetsport.ma - Fichiers Railway (Stealth Mode)
📄 app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time
import base64
import os
import random

app = Flask(__name__)
CORS(app)

# User-Agents réalistes (navigateurs récents)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

@app.route('/generate', methods=['POST'])
def generate_barcode():
    data = request.json
    matches = data.get('matches', [])
    mise = data.get('mise', '10')

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--ignore-certificate-errors',
                    '--ignore-certificate-errors-spki-list',
                    '--disable-web-security',
                    '--allow-running-insecure-content',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                ]
            )

            user_agent = random.choice(USER_AGENTS)

            context = browser.new_context(
                ignore_https_errors=True,
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='fr-FR',
                timezone_id='Africa/Casablanca',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,ar;q=0.6',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                }
            )

            page = context.new_page()

            # Appliquer le mode stealth (masque les traces d'automatisation)
            stealth_sync(page)

            # Naviguer vers le site
            page.goto('http://coteetsport.ma', timeout=60000, wait_until='networkidle')

            # Pause réaliste pour simuler un humain
            time.sleep(random.uniform(2, 4))

            for match_data in matches:
                match_name = match_data.get('match', '')
                prono = match_data.get('prono', '')

                search_input = page.query_selector('input[type="search"], input[placeholder*="cherch"]')
                if search_input:
                    # Simuler une frappe humaine
                    search_input.click()
                    time.sleep(random.uniform(0.3, 0.8))
                    search_term = match_name.split(' vs ')[0] if ' vs ' in match_name else match_name.split(' - ')[0]
                    for char in search_term:
                        search_input.type(char, delay=random.randint(50, 150))
                    time.sleep(random.uniform(1.5, 3))

                prediction_btn = page.query_selector(f'[data-outcome="{prono}"], button:has-text("{prono}")')
                if prediction_btn:
                    prediction_btn.click()
                    time.sleep(random.uniform(0.8, 1.5))

            mise_input = page.query_selector('input[name="mise"], input[placeholder*="mise"]')
            if mise_input:
                mise_input.click()
                time.sleep(random.uniform(0.2, 0.5))
                mise_input.fill(str(mise))

            generate_btn = page.query_selector('button:has-text("Generer"), button:has-text("Reserver")')
            if generate_btn:
                generate_btn.click()
                time.sleep(random.uniform(4, 6))

            barcode_element = page.query_selector('.barcode, [class*="barcode"], img[alt*="code"]')
            if barcode_element:
                screenshot = barcode_element.screenshot()
                barcode_b64 = base64.b64encode(screenshot).decode('utf-8')
                browser.close()
                return jsonify({
                    "status": "success",
                    "barcode_url": f"data:image/png;base64,{barcode_b64}"
                })

            # Capture de la page entière comme fallback
            screenshot = page.screenshot(full_page=True)
            barcode_b64 = base64.b64encode(screenshot).decode('utf-8')
            browser.close()
            return jsonify({
                "status": "success",
                "barcode_url": f"data:image/png;base64,{barcode_b64}"
            })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
