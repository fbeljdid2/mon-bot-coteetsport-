 app.py
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

REALISTIC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

def human_type(page, selector, text):
    element = page.query_selector(selector)
    if element:
        element.click()
        time.sleep(random.uniform(0.3, 0.7))
        for char in text:
            element.type(char, delay=random.randint(50, 150))
            time.sleep(random.uniform(0.05, 0.15))

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
                    '--disable-blink-features=AutomationControlled',
                    '--ignore-certificate-errors',
                    '--ignore-certificate-errors-spki-list',
                    '--disable-web-security',
                    '--allow-running-insecure-content'
                ]
            )
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent=REALISTIC_HEADERS["User-Agent"],
                viewport={"width": 1366, "height": 768},
                locale="fr-FR",
                timezone_id="Africa/Casablanca",
                extra_http_headers=REALISTIC_HEADERS
            )
            page = context.new_page()
            stealth_sync(page)

            page.goto('http://coteetsport.ma', timeout=60000)
            page.wait_for_load_state('networkidle')
            time.sleep(random.uniform(2, 4))

            for match_data in matches:
                match_name = match_data.get('match', '')
                prono = match_data.get('prono', '')

                search_input = page.query_selector('input[type="search"], input[placeholder*="cherch"]')
                if search_input:
                    search_input.fill(match_name.split(' vs ')[0])
                    time.sleep(random.uniform(1.5, 3))

                prediction_btn = page.query_selector(f'[data-outcome="{prono}"], button:has-text("{prono}")')
                if prediction_btn:
                    prediction_btn.click()
                    time.sleep(random.uniform(0.8, 1.5))

            mise_input = page.query_selector('input[name="mise"], input[placeholder*="mise"]')
            if mise_input:
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

            screenshot = page.screenshot()
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
