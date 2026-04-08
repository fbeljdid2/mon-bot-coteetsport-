from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import time
import base64
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"status": "Bot actif", "routes": ["/health", "/generate"]})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/generate', methods=['POST'])
def generate_barcode():
    data = request.json
    matches = data.get('matches', [])
    mise = data.get('mise', '10')

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            page = browser.new_page()
            page.goto('https://coteetsport.ma', timeout=60000)
            page.wait_for_load_state('networkidle')

            for match_data in matches:
                match_name = match_data.get('match', '')
                prono = match_data.get('prono', '')

                search_input = page.query_selector('input[type="search"], input[placeholder*="cherch"], input[placeholder*="Cherch"]')
                if search_input:
                    search_input.fill('')
                    search_input.fill(match_name.split(' vs ')[0] if ' vs ' in match_name else match_name.split(' - ')[0])
                    time.sleep(3)

                prediction_btn = page.query_selector(f'[data-outcome="{prono}"], button:has-text("{prono}")')
                if prediction_btn:
                    prediction_btn.click()
                    time.sleep(1)

            mise_input = page.query_selector('input[name="mise"], input[placeholder*="mise"], input[placeholder*="Mise"], input[type="number"]')
            if mise_input:
                mise_input.fill('')
                mise_input.fill(str(mise))

            generate_btn = page.query_selector('button:has-text("GÃ©nÃ©rer"), button:has-text("RÃ©server"), button:has-text("Valider")')
            if generate_btn:
                generate_btn.click()
                time.sleep(5)

            barcode_element = page.query_selector('.barcode, [class*="barcode"], img[alt*="code"], [class*="ticket"], [class*="reservation"]')
            if barcode_element:
                screenshot = barcode_element.screenshot()
                barcode_b64 = base64.b64encode(screenshot).decode('utf-8')
                browser.close()
                return jsonify({
                    "status": "success",
                    "barcode_url": f"data:image/png;base64,{barcode_b64}"
                })

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
