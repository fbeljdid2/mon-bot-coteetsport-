import os
import logging
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

# Configuration des logs pour Railway
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app) # Autorise Lovable et Base44 à communiquer avec le bot

@app.route('/')
@app.route('/health')
def home():
    return "Le bot MDJS est en ligne et prêt !", 200

def get_mdjs_reservation(match_name, prono_val):
    with sync_playwright() as p:
        # Lancement du navigateur en mode discret
        browser = p.chromium.launch(headless=True)
        # Simulation d'un utilisateur sur mobile pour éviter les blocages
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()
        
        try:
            logging.info(f"Début de la recherche pour : {match_name} ({prono_val})")
            
            # 1. Aller sur le site
            page.goto("https://coteetsport.ma", timeout=60000, wait_until="networkidle")

            # 2. Fermer les éventuelles fenêtres publicitaires
            try:
                page.click("button[aria-label='Close']", timeout=3000)
            except:
                pass

            # 3. Recherche du match
            # Note: On cherche l'icône de recherche ou on tape directement si le champ est visible
            page.wait_for_selector("input", timeout=10000)
            page.type('input', match_name)
            page.keyboard.press("Enter")
            time.sleep(4) # Attente du chargement des résultats

            # 4. Sélection du pronostic (1, X ou 2)
            # On cherche le texte du match d'abord pour être sûr
            page.click(f"text={match_name}")
            time.sleep(2)
            
            # On clique sur la cote choisie
            # Le site utilise souvent des boutons avec la classe .odds-value
            page.locator(".odds-value").filter(has_text=prono_val).first.click()
            time.sleep(2)

            # 5. Cliquer sur "Réserver" (Bouton blanc de votre image)
            # On utilise le texte exact car les IDs changent souvent
            page.click("button:has-text('Réserver')")
            time.sleep(4)

            # 6. Récupération du CODE de réservation
            # On attend que l'élément contenant le code apparaisse (ex: "A123B")
            # Ajustez '.reservation-code' si le nom technique change
            code_element = page.wait_for_selector(".reservation-code, .booking-id", timeout=15000)
            res_code = code_element.inner_text()
            
            # On cherche l'URL de l'image du QR Code pour l'afficher dans Lovable
            qr_element = page.query_selector("img[src*='qr']")
            qr_url = qr_element.get_attribute("src") if qr_element else "Pas de QR code trouvé"

            browser.close()
            return {"status": "success", "code": res_code, "barcode_url": qr_url}

        except Exception as e:
            logging.error(f"Erreur Playwright : {str(e)}")
            # En cas d'erreur, on ferme proprement le navigateur
            browser.close()
            return {"status": "error", "message": str(e)}

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Données JSON manquantes"}), 400

    match = data.get("match")
    prono = data.get("prono")

    if not match or not prono:
        return jsonify({"status": "error", "message": "Champs 'match' ou 'prono' manquants"}), 400

    # Lancement du bot
    result = get_mdjs_reservation(match, prono)

    if result["status"] == "success":
        return jsonify({
            "status": "success",
            "reservation_code": result["code"],
            "barcode_url": result["barcode_url"]
        })
    else:
        return jsonify({
            "status": "error",
            "details": result["message"]
        }), 500

if __name__ == '__main__':
    # Railway définit automatiquement le PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
