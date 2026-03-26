import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app)

# Variables Railway
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Bot MDJS pret"})

@app.route('/generer-barcode', methods=['POST'])
def generer_barcode():
    data = request.get_json()
    if not data:
        return jsonify({"status": "erreur", "message": "Aucun match recu"}), 400

    matches_a_chercher = data if isinstance(data, list) else [data]

    with sync_playwright() as p:
        # Configuration sans 'stealth' pour tester la stabilite d'abord
        try:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = context.new_page()

            # 1. Aller sur le site
            page.goto('https://www.coteetsport.ma', timeout=60000)
            
            # 2. Tentative de clic sur Connexion
            try:
                page.wait_for_selector('text="Connexion"', timeout=10000)
                page.click('text="Connexion"')
                page.fill('input[name="email"]', EMAIL)
                page.fill('input[name="password"]', PASSWORD)
                page.click('button[type="submit"]')
                page.wait_for_timeout(3000)
            except:
                print("Etape connexion ignoree ou bouton non trouve")

            # 3. Ajout des matchs
            matches_ajoutes = []
            for item in matches_a_chercher:
                nom = item.get("match")
                if nom:
                    try:
                        selector = f'text=/{nom}/i'
                        page.click(selector, timeout=5000)
                        matches_ajoutes.append(nom)
                    except:
                        continue

            # 4. Generer le code
            page.click('button:has-text("Générer"), button:has-text("Valider")', timeout=5000)
            page.wait_for_timeout(3000)
            
            # Recuperation du code
            code_final = page.locator('.reservation-code, .code-value').first.inner_text()

            browser.close()
            return jsonify({"status": "success", "barcode": code_final.strip()})

        except Exception as e:
            return jsonify({"status": "erreur", "message": str(e)}), 500

if __name__ == "__main__":
    # IMPORTANT : Railway impose le port
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
