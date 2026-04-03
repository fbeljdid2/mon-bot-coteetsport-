 from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)

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
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page()

            # Navigue vers le site et remplis le formulaire
            page.goto("https://www.coteetsport.ma", timeout=60000)
            # --- Adapte ici selon le formulaire reel du site ---
            # page.fill("#match-input", match)
            # page.fill("#prono-input", prono)
            # page.fill("#mise-input", mise)
            # page.click("#submit-btn")
            # page.wait_for_selector("#barcode-img", timeout=60000)
            # barcode_url = page.get_attribute("#barcode-img", "src")

            # Placeholder - remplace par ta vraie logique
            barcode_url = "https://via.placeholder.com/300x100?text=BARCODE"

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
