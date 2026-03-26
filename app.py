import os
import time
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

app = Flask(__name__)

# Identifiants sécurisés de Railway
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

@app.route('/')
def home():
    # Réponse en JSON pur pour que Base44 ne crash pas
    return jsonify({
        "status": "online",
        "message": "Bot Paris Match IA pret",
        "endpoint": "/generer-barcode"
    })

@app.route('/generer-barcode', methods=['POST'])
def generer_barcode():
    # On récupère les pronostics envoyés par Base44
    data = request.get_json()
    if not data:
        return jsonify({"status": "erreur", "message": "Aucune donnee recue"}), 400

    with sync_playwright() as p:
        # Lancement du navigateur
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page) # Pour ne pas être détecté comme robot

        try:
            # 1. Aller sur le site officiel
            page.goto('https://www.coteetsport.ma', wait_until="networkidle")
            
            # 2. Connexion (Login)
            # On cherche le bouton connexion par le texte
            page.click('text="Connexion"') 
            page.wait_for_selector('input[name="email"]', timeout=5000)
            page.fill('input[name="email"]', EMAIL)
            page.fill('input[name="password"]', PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)

            # 3. Ajouter les matchs au panier
            # On parcourt la liste envoyée par ton app
            matches_ajoutes = []
            for item in data:
                nom_match = item.get("match")
                if nom_match:
                    # On cherche le texte du match et on clique sur la cote
                    try:
                        page.click(f'text="{nom_match}"', timeout=3000)
                        matches_ajoutes.append(nom_match)
                    except:
                        continue # Si le match n'est pas trouvé, on passe au suivant

            # 4. Aller au panier et générer le code
            # Note : l'URL exacte du panier est souvent /panier ou /cart
            page.goto('https://www.coteetsport.ma', wait_until="networkidle")
            
            # Cliquer sur le bouton pour générer le code de réservation
            # On cherche un bouton qui contient "Générer" ou "Valider"
            page.click('button:has-text("Générer"), button:has-text("Valider")')
            page.wait_for_timeout(4000)

            # 5. Récupérer le code de réservation final
            # On cherche l'élément qui contient le code (souvent une classe 'reservation-code')
            resultat_code = page.locator('.reservation-code, .code-value').first.inner_text()

            browser.close()
            return jsonify({
                "status": "success",
                "barcode": resultat_code,
                "matches": matches_ajoutes
            })

        except Exception as e:
            browser.close()
            return jsonify({"status": "erreur", "message": str(e)}), 500

if __name__ == "__main__":
    # Configuration du port pour Railway
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
