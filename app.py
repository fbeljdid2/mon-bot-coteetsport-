import os
from flask import Flask, request, jsonify
from flask_cors import CORS  # Permet la connexion avec l'application mobile
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

app = Flask(__name__)
CORS(app) # Autorise ton application à parler au bot Railway

# Identifiants Railway
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Bot Paris Match IA pret pour SISAL",
        "endpoint": "/generer-barcode"
    })

@app.route('/generer-barcode', methods=['POST'])
def generer_barcode():
    # On récupère les matchs envoyés par l'application
    data = request.get_json()
    if not data:
        return jsonify({"status": "erreur", "message": "Aucun match recu"}), 400

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        stealth_sync(page)

        try:
            # 1. Aller sur le site Sisal MDJS
            page.goto('https://www.coteetsport.ma', wait_until="networkidle")
            
            # 2. Connexion automatique
            page.click('text="Connexion"')
            page.wait_for_selector('input[name="email"]')
            page.fill('input[name="email"]', EMAIL)
            page.fill('input[name="password"]', PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)

            # 3. Ajout des matchs au panier
            # Si data est une liste : [{"match": "Safi vs Berkane"}]
            matches_ajoutes = []
            for item in data:
                nom_match = item.get("match")
                if nom_match:
                    # On clique sur le nom du match pour l'ajouter
                    page.click(f'text="{nom_match}"', timeout=4000)
                    matches_ajoutes.append(nom_match)
                    page.wait_for_timeout(1000)

            # 4. Générer le code de réservation final
            page.goto('https://www.coteetsport.ma')
            page.click('button:has-text("Générer"), button:has-text("Valider")')
            page.wait_for_timeout(5000)
            
            # On récupère le texte du code (ex: A123B45)
            code_final = page.locator('.reservation-code, .code-value').first.inner_text()

            browser.close()
            return jsonify({
                "status": "success",
                "barcode": code_final,
                "matches": matches_ajoutes
            })

        except Exception as e:
            browser.close()
            return jsonify({"status": "erreur", "message": str(e)}), 500
if __name__ == "__main__":
    # On utilise le port que Railway nous donne ou 8080 par défaut
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

