from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os
import base64

app = Flask(__name__)

MDJS_EMAIL = os.environ.get("MDJS_EMAIL", "")
MDJS_PASSWORD = os.environ.get("MDJS_PASSWORD", "")

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    match = data.get("match", "")        # ex: "Constantine vs Oran"
    prono = data.get("prono", "")        # ex: "X" ou "1" ou "2"
    mise = data.get("mise", "10")        # ex: "20"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context()
            page = context.new_page()

            # 1. Connexion
            page.goto("https://zonereservee.coteetsport.ma/login", timeout=60000)
            page.fill("input[type='email'], input[name='email'], #email", MDJS_EMAIL)
            page.fill("input[type='password'], input[name='password'], #password", MDJS_PASSWORD)
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle", timeout=30000)

            # 2. Aller sur Cote & Sport
            page.goto("https://www.coteetsport.ma/cote-sport", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)

            # 3. Chercher le match par nom
            teams = match.split(" vs ")
            home_team = teams[0].strip() if len(teams) > 0 else match

            match_element = page.locator(f"text={home_team}").first
            if match_element:
                match_element.click()
                page.wait_for_load_state("networkidle", timeout=15000)

            # 4. Selectionner le pronostic (1, X, 2)
            prono_map = {"1": 0, "X": 1, "2": 2}
            prono_index = prono_map.get(prono.upper(), 0)

            bet_buttons = page.locator(".odd-button, .cote-button, [class*='odd'], [class*='bet']").all()
            if len(bet_buttons) > prono_index:
                bet_buttons[prono_index].click()
                page.wait_for_timeout(2000)

            # 5. Entrer la mise
            mise_input = page.locator("input[placeholder*='mise'], input[placeholder*='montant'], .stake-input").first
            if mise_input:
                mise_input.fill(str(mise))
                page.wait_for_timeout(1000)

            # 6. Valider le pari
            page.locator("button:has-text('Valider'), button:has-text('Jouer'), button:has-text('Confirmer')").first.click()
            page.wait_for_timeout(5000)

            # 7. Capturer le code-barres
            barcode_element = page.locator("[class*='barcode'], [class*='code-barre'], canvas, img[alt*='barcode'], img[alt*='code']").first

            if barcode_element and barcode_element.is_visible():
                barcode_bytes = barcode_element.screenshot()
                barcode_b64 = base64.b64encode(barcode_bytes).decode('utf-8')
                barcode_url = f"data:image/png;base64,{barcode_b64}"
            else:
                page_bytes = page.screenshot()
                barcode_b64 = base64.b64encode(page_bytes).decode('utf-8')
                barcode_url = f"data:image/png;base64,{barcode_b64}"

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
