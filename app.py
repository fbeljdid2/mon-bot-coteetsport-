import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

app = Flask(__name__)
CORS(app)

# Identifiants récupérés depuis les variables Railway
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Bot MDJS prêt"})

@app.route('/generer-barcode', methods=['POST'])
def generer_barcode():
    data = request.get_json()
    if not data:
        return jsonify({"status": "erreur", "message": "Aucun match reçu"}), 400

    # Si Lovable envoie un seul match, on le transforme en liste
    matches_a_chercher = data if isinstance(data, list) else [data]

    with sync_playwright() as p:
        # Lancement du navigateur avec options pour éviter la détection
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        stealth_sync(page)

        try:
            # 1. Connexion au site MDJS
            page.goto('https://www.coteetsport.ma', wait_until="networkidle", timeout=60000)
            
            # Cliquer sur connexion (on gère si le bouton est déjà là ou dans un menu)
            if page.locator('text="Connexion"').is_visible():
                page.click('text="Connexion"')
                page.fill('input[name="email"]', EMAIL)
                page.fill('input[name="password"]', PASSWORD)
                page.click('button[type="submit"]')
                page.wait_for_timeout(3000)

            # 2. Ajout des matchs au panier (Recherche flexible)
            matches_ajoutes = []
            for item in matches_a_chercher:
                nom_match = item.get("match")
                if nom_match:
                    try:
                        # On cherche un texte qui CONTIENT le nom (ex: "Safi" trouvera "OCS SAFI")
                        # L'option /i rend la recherche insensible aux majuscules
                        selector = f'text=/{nom_match}/i'
                        page.wait_for_selector(selector, timeout=8000)
                        page.click(selector)
                        matches_ajoutes.append(nom_match)
                        page.wait_for_timeout(1500)
                    except:
                        print(f"Match non trouvé : {nom_match}")

            if not matches_ajoutes:
                return jsonify({"status": "erreur", "message": "Aucun match correspondant trouvé sur le site"}), 404

            # 3. Génération du code de réservation
            # On clique sur le panier ou le bouton de validation
            page.locator('button.btn-bet-slip, .cart-icon').first.click()
            page.wait_for_timeout(2000)
            
            # Cliquer sur "Générer le code" ou "Réserver"
            page.click('button:has-text("Générer"), button:has-text("Réserver"), button:has-text("Valider")')
            page.wait_for_timeout(5000)
            
            # 4. Récupération du code final (Sélecteur à adapter selon le site MDJS actuel)
            # On essaie de trouver le texte qui ressemble à un code de réservation
            code_final = page.locator('.reservation-code, .code-value, h2.code').first.inner_text()

            browser.close()
            return jsonify({
                "status": "success",
                "barcode": code_final.strip(),
                "matches": matches_ajoutes
            })

        except Exception as e:
            if 'browser' in locals(): browser.close()
            return jsonify({"status": "erreur", "message": str(e)}), 500

if __name__ == "__main__":
    # Crucial pour Railway : écouter sur le port injecté par l'environnement
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
