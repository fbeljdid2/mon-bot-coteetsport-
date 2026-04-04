from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os
import base64
import time

app = Flask(__name__)

# ====== METS TES IDENTIFIANTS ICI ======
MDJS_EMAIL = os.environ.get("MDJS_EMAIL", "ton_email@gmail.com")
MDJS_PASSWORD = os.environ.get("MDJS_PASSWORD", "ton_mot_de_passe")
# ======================================

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    match = data.get("match", "")
    prono = data.get("prono", "")
    mise = data.get("mise", "")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()

            # 1. Se connecter
            page.goto("https://zonereservee.coteetsport.ma/login", timeout=60000, wait_until="networkidle")
            time.sleep(2)

            page.fill("input[type='email'], input[name='username'], #username", MDJS_EMAIL)
            page.fill("input[type='password'], input[name='password'], #password", MDJS_PASSWORD)
            page.click("button[type='submit'], input[type='submit']")
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)

            # 2. Prendre screenshot du billet/confirmation (adapter selon le vrai flux du site)
            screenshot_bytes = page.screenshot(full_page=False)
            b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            barcode_url = f"data:image/png;base64,{b64}"

            browser.close()

        return jsonify({"status": "success", "barcode_url": barcode_url})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
