import os
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

# Récupère tes identifiants configurés sur Railway
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

@app.route('/')
def home():
    return "Bot prêt pour générer code-barres SISAL !"

@app.route('/generer-barcode', methods=['POST'])
def generer_barcode():
    # Reçoit les matchs de ton app Lovable : [{"match": "Real-Barca", "cote": "1"}]
    data = request.get_json()
    
    with sync_playwright() as p:
        # Lancer le navigateur installé par Railway
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. Aller sur le site officiel
            page.goto('https://www.coteetsport.ma', wait_until="networkidle")
            
            # 2. Se connecter (Login)
            page.click('text="Connexion"') # Clique sur le bouton Connexion
            page.fill('input[name="email"]', EMAIL)
            page.fill('input[name="password"]', PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(2000)

            # 3. Ajouter les matchs au panier (Simulation)
            for pred in data:
                # Chercher le match par son nom et cliquer sur la cote
                page.click(f'text="{pred["match"]}"')
                page.wait_for_timeout(1000)

            # 4. Aller au panier et générer le code de réservation
            page.goto('https://www.coteetsport.ma')
            page.click('button:has-text("Générer")')
            page.wait_for_timeout(3000)

            # 5. Récupérer l'image ou le texte du code-barres
            barcode = page.locator('.reservation-code').inner_text()
            
            browser.close()
            return jsonify({"status": "succès", "barcode": barcode})

        except Exception as e:
            browser.close()
            return jsonify({"status": "erreur", "message": str(e)}), 500
if __name__ == "__main__":
    # Très important pour Railway :
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

