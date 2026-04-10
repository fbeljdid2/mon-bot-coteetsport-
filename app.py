from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import time
import base64
import os

app = Flask(__name__)
CORS(app)

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
                    '--allow-running-insecure-content'
                ]
            )
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            page.goto('http://coteetsport.ma', timeout=60000)
            page.wait_for_load_state('networkidle')

            for match_data in matches:
                match_name = match_data.get('match', '')
                prono = match_data.get('prono', '')

                search_input = page.query_selector('input[type="search"], input[placeholder*="cherch"]')
                if search_input:
                    search_input.fill(match_name.split(' vs ')[0])
                    time.sleep(2)

                prediction_btn = page.query_selector(f'[data-outcome="{prono}"], button:has-text("{prono}")')
                if prediction_btn:
                    prediction_btn.click()
                    time.sleep(1)

            mise_input = page.query_selector('input[name="mise"], input[placeholder*="mise"]')
            if mise_input:
                mise_input.fill(str(mise))

            generate_btn = page.query_selector('button:has-text("Generer"), button:has-text("Reserver")')
            if generate_btn:
                generate_btn.click()
                time.sleep(5)

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
