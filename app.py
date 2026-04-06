from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import time, os

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_barcode():
    data = request.json
    matches = data.get('matches', [])
    mise = data.get('mise', '10')
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://coteetsport.ma')
            time.sleep(3)
            
            for match in matches:
                # Fill match and prediction
                # This is a template - customize for coteetsport.ma
                pass
            
            # Set mise amount
            # Click generate barcode
            # Wait for barcode
            # Screenshot barcode
            
            page.screenshot(path='barcode.png')
            browser.close()
        
        # Upload and return URL
        return jsonify({"status": "success", "barcode_url": "URL_HERE"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
