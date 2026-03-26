import os
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

app = Flask(__name__)

# Identifiants Railway (EMAIL et PASSWORD)
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

@app.route('/')
def home():
    # Réponse en JSON pour éviter les erreurs de lecture de Base44
    return jsonify({
        "status": "online",
        "bot": "Paris Match IA",
        "message": "En attente de pronostics sur /generer-barcode"
    })

@app.route('/generer-barcode', methods=['POST'])
def generer_barcode():
    data = request.get_json()
    if not data:
        return jsonify({"status": "erreur", "message": "Aucune donnee recue"}), 400

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        stealth_sync(page)

        try:
            # 1. Connexion au site Sisal
            page.goto('https://www.coteetsport.ma', wait_until="networkidle")
            page.click('text="Connexion"')
            page.fill('input[name="email"]', EMAIL)
            page.fill('input[name="password"]', PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)

            # 2. Ajout des pronostics au panier
            for item in data:
                nom_match = item.get("match")
                if nom_match:
                    page.click(f'text="{nom_match}"', timeout=3000)
                    page.wait_for_timeout(1000)

            # 3. Récupération du code de réservation
            page.goto('https://www.coteetsport.ma')
            page.click('button:has-text("Générer")')
            page.wait_for_timeout(4000)
            
            # On récupère le texte du code généré
            code_final = page.locator('.reservation-code').first.inner_text()

            browser.close()
            return jsonify({"status": "success", "barcode": code_final})

        except Exception as e:
            browser.close()
            return jsonify({"status": "erreur", "message": str(e)}), 500

if __name__ == "__main__":
    # FORCE LE PORT 8080 POUR ÉVITER LE CRASH RAILWAY
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
