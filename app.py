from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import base64
import os
import time

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    matches = data.get('matches', [])
    stake = str(data.get('stake', 10))

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()

            page.goto('https://coteetsport.ma', timeout=60000, wait_until='domcontentloaded')
            time.sleep(4)

            for match_data in matches:
                match_name = match_data.get('match', '')
                prono = match_data.get('prono', '')

                # Try search input
                try:
                    search_sel = 'input[type="search"], input[placeholder*="echerch"], input[name*="search"]'
                    page.wait_for_selector(search_sel, timeout=5000)
                    page.fill(search_sel, match_name)
                    time.sleep(2)
                except Exception:
                    pass

                # Click prediction if visible
                try:
                    page.click(f'text={prono}', timeout=5000)
                    time.sleep(1)
                except Exception:
                    pass

            # Set stake
            try:
                mise_sel = 'input[type="number"]'
                page.wait_for_selector(mise_sel, timeout=5000)
                page.fill(mise_sel, stake)
                time.sleep(1)
            except Exception:
                pass

            # Click generate/reserve button
            try:
                btn_sel = 'button:has-text("Générer"), button:has-text("Réserver"), button:has-text("Valider"), button:has-text("Imprimer")'
                page.click(btn_sel, timeout=8000)
                time.sleep(5)
            except Exception:
                pass

            # Try to grab barcode element screenshot
            barcode_b64 = None
            reservation_code = ""

            barcode_selectors = [
                'canvas',
                'img[alt*="barcode"], img[alt*="code"], img[src*="barcode"]',
                'svg[class*="barcode"]',
                '.barcode, .code-barre, .reservation-barcode, .ticket-barcode',
                '#barcode, #code-barre'
            ]

            for sel in barcode_selectors:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        img_bytes = el.screenshot()
                        barcode_b64 = base64.b64encode(img_bytes).decode('utf-8')
                        break
                except Exception:
                    continue

            # Fallback: full page screenshot
            if not barcode_b64:
                img_bytes = page.screenshot(full_page=False)
                barcode_b64 = base64.b64encode(img_bytes).decode('utf-8')

            # Try to get reservation code text
            code_selectors = [
                '.reservation-code, .code-reservation, .ticket-code, .numero-reservation',
                'span[class*="code"], p[class*="code"], div[class*="code"]'
            ]
            for sel in code_selectors:
                try:
                    el = page.query_selector(sel)
                    if el:
                        reservation_code = el.inner_text().strip()
                        break
                except Exception:
                    continue

            browser.close()

            return jsonify({
                'status': 'success',
                'barcode_url': f'data:image/png;base64,{barcode_b64}',
                'reservation_code': reservation_code
            })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
