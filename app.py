import os
import logging
import time
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

# Configuration des logs pour Railway
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def home():
    return "Bot MDJS en ligne !", 200

def get_mdjs_reservation(match_name, prono_val):
    with sync_playwright() as p:
        # Configuration pour mobile/évitement de détection
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()
        
        try:
            logging.info(f"Recherche de : {match_name}")
            page.goto("https://coteetsport.ma", timeout=60000, wait_until="networkidle")

            # 1. Fermer les pubs/popups si elles apparaissent
            try:
                page.click("button[aria-label='Close']", timeout=5000)
            except:
                pass

            # 2. Utiliser la barre de recherche
            page.click(".search-icon") # Cliquer sur la loupe
            page.fill("input[type='search']", match_name)
            page.keyboard.press("Enter")
            time.sleep(3) # Attente visuelle du chargement

            # 3. Cliquer sur le match trouvé
            page.click(f"text={match_name}")
            time.sleep(2)

            # 4. Sélectionner le prono (1, X ou 2)
            # On cherche le bouton qui contient exactement le texte du prono
            page.locator(".odds-value").filter(has_text=prono_val).first.click()
            time.sleep(2)

            # 5. Cliquer sur "Réserver" (Bouton blanc de votre image)
            # Utilise le texte exact 'Réserver'
            page.click("button:has-text('Réserver')")
            time.sleep(3)

            # 6. Récupérer le code de réservation ou le QR Code
            # Le site affiche souvent un élément avec une classe 'booking-code'
            # On essaie de prendre une capture d'écran pour le debug si ça rate
            try:
                # On cherche l'élément qui contient le code (souvent en gras)
                reservation_element = page.wait_for_selector(".reservation-code", timeout=10000)
                res_code = reservation_element.inner_text()
                
                # On cherche l'URL de l'image du QR Code
                qr_element = page.query_selector("img.qr-code")
                qr_url = qr_element.get_attribute("src") if qr_element else ""

                browser.close()
                return {"status": "success", "code": res_code, "url": qr_url}
            
            except Exception as e:
                # Si on ne trouve pas le code, on renvoie une erreur détaillée
                browser.close()
                return {"status": "error", "message": "Code non trouvé après clic sur Réserver"}

        except Exception as e:
            logging.error(f"Erreur : {str(e)}")
            browser.close()
            return {"status": "error", "message": str(e)}

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "JSON vide"}), 400

    match = data.get("match")
    prono = data.get("prono")

    result = get_mdjs_reservation(match, prono)

    if result["status"] == "success":
        return jsonify({
            "status": "success",
            "reservation_code": result["code"],
            "barcode_url": result["url"]
        })
    else:
        return jsonify({"status": "error", "details": result["message"]}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
