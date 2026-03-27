import os
import sys
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

app = Flask(__name__)
# Autorise Lovable à communiquer avec ce serveur
CORS(app, resources={r"/*": {"origins": "*"}})

# Variables Railway (Assure-toi de les remplir dans l'onglet Settings > Variables sur Railway)
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Bot MDJS prêt pour Lovable"})

@app.route('/generer-barcode', methods=['POST'])
def generer_barcode():
    # 1. Récupération des données envoyées par Lovable
    raw_data = request.get_json()
    if not raw_data:
        return jsonify({"status": "erreur", "message": "Aucune donnée reçue"}), 400

    # Lovable envoie souvent {"matches": [liste_des_matchs]}
    if isinstance(raw_data, dict) and "matches" in raw_data:
        matches_a_chercher = raw_data["matches"]
    else:
        matches_a_chercher = raw_data if isinstance(raw_data, list) else [raw_data]

    with sync_playwright() as p:
        try:
            # Lancement du navigateur configuré pour Railway
            browser = p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()

            # Aller sur le site officiel
            print("Accès au site MDJS...")
            page.goto('https://www.coteetsport.ma', timeout=60000, wait_until="networkidle")
            
            # (Optionnel) Connexion si les accès sont fournis
            if EMAIL and PASSWORD:
                try:
                    page.click('text="Connexion"', timeout=5000)
                    page.fill('input[type="email"]', EMAIL)
                    page.fill('input[type="password"]', PASSWORD)
                    page.click('button[type="submit"]')
                    page.wait_for_timeout(2000)
                except:
                    print("Connexion ignorée")

            # 2. Remplissage du panier
            for item in matches_a_chercher:
                # On cherche le nom de l'équipe (ex: "Tigre")
                nom_equipe = item.get("awayTeam") or item.get("homeTeam") or item.get("match")
                if nom_equipe:
                    try:
                        # On cherche le texte et on clique sur la cote
                        page.get_by_text(nom_equipe, exact=False).first.click(timeout=5000)
                        print(f"Match ajouté : {nom_equipe}")
                        page.wait_for_timeout(1000)
                    except Exception as e:
                        print(f"Impossible de trouver {nom_equipe}")

            # 3. Génération du code de réservation
            # On clique sur le bouton du panier / valider
            print("Génération du code...")
            page.click('button:has-text("Réserver"), .btn-reserver', timeout=10000)
            
            # Attendre que le code apparaisse à l'écran
            page.wait_for_selector('.reservation-code, .code-value, #barcode', timeout=15000)
            
            # Récupérer le texte du code
            code_final = page.locator('.reservation-code, .code-value, #barcode').first.inner_text()
            
            # Optionnel : Prendre une capture d'écran du code-barres pour Lovable
            # page.locator('#barcode-img').screenshot(path="barcode.png")

            browser.close()
            
            return jsonify({
                "status": "success", 
                "barcode": code_final.strip(),
                "message": "Code généré avec succès"
            })

        except Exception as e:
            print(f"Erreur : {str(e)}")
            return jsonify({"status": "erreur", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
