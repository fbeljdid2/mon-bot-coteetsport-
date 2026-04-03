import os
import logging
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

# Configuration des logs pour Railway
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
# Autorise explicitement toutes les origines pour éviter les erreurs CORS avec Lovable
CORS(app, resources={r"/*": {"origins": "*"}}) 

@app.route('/')
@app.route('/health')
def home():
    return "Le bot MDJS est en ligne et prêt !", 200

def get_mdjs_reservation(match_name, prono_val, mise_val):
    with sync_playwright() as p:
        # Lancement du navigateur
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            logging.info(f"Traitement : {match_name} | Prono: {prono_val} | Mise: {mise_val}")
            
            # 1. Aller sur le site
            page.goto("https://coteetsport.ma", timeout=60000, wait_until="networkidle")

            # 2. Fermer les popups (Cookie ou Pub)
            try:
                page.click("button:has-text('Accepter'), button[aria-label='Close']", timeout=5000)
            except:
                pass

            # 3. Recherche du match
            search_input = page.wait_for_selector("input[placeholder*='recherche'], input", timeout=15000)
            search_input.fill(match_name)
            page.keyboard.press("Enter")
            time.sleep(3)

            # 4. Sélection du match et du pronostic
            # On clique sur le match trouvé
            page.click(f"text={match_name}", timeout=10000)
            time.sleep(2)
            
            # Clic sur la cote (1, X, ou 2)
            page.locator(".odds-value").filter(has_text=prono_val).first.click()
            time.sleep(2)

            # 5. Saisie de la MISE
            # On cherche le champ de saisie de la mise dans le panier
            try:
                stake_input = page.locator("input.stake-input, input[placeholder*='Mise']").first
                stake_input.fill(str(mise_val))
                time.sleep(1)
            except:
                logging.warning("Champ de mise non trouvé, continuation avec mise par défaut.")

            # 6. Cliquer sur "Réserver"
            page.click("button:has-text('Réserver')", timeout=10000)
            time.sleep(5) # Attente de la génération du QR Code

            # 7. Récupération des données finales
            # On récupère le texte du code
            res_code = "Non trouvé"
            try:
                code_element = page.wait_for_selector(".reservation-code, .booking-id", timeout=10000)
                res_code = code_element.inner_text()
            except:
                pass
            
            # On récupère l'URL de l'image du QR Code
            qr_url = ""
            qr_element = page.query_selector("img[src*='qr'], .qr-code img")
            if qr_element:
                qr_url = qr_element.get_attribute("src")
                # Si l'URL est relative (ex: /images/qr.png), on ajoute le domaine
                if qr_url.startswith('/'):
                    qr_url = "https://coteetsport.ma" + qr_url

            browser.close()
            return {"status": "success", "code": res_code, "barcode_url": qr_url}

        except Exception as e:
            logging.error(f"Erreur Playwright : {str(e)}")
            browser.close()
            return {"status": "error", "message": str(e)}

@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    # Gestion de la requête de pré-vérification CORS
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Données JSON manquantes"}), 400

    match = data.get("match")
    prono = data.get("prono")
    mise = data.get("mise", "10") # 10 par défaut si non précisé

    if not match or not prono:
        return jsonify({"status": "error", "message": "Champs 'match' ou 'prono' manquants"}), 400

    # Lancement du bot
    result = get_mdjs_reservation(match, prono, mise)

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
