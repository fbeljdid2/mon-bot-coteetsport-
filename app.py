import os
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

def get_sisal_barcode(match_name, prono_val):
    with sync_playwright() as p:
        # Lancement du navigateur (mode sans interface pour Railway)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. Aller sur le site officiel
            page.goto("https://coteetsport.ma", timeout=60000)
            
            # 2. Rechercher le match (simulation de frappe dans la barre de recherche)
            # Note: Le site MDJS est complexe, on cherche ici le texte du match
            page.get_by_placeholder("Rechercher un match").fill(match_name)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000) # Attendre que les résultats s'affichent

            # 3. Cliquer sur le pronostic (Ex: "1", "X", ou "2")
            # On cherche un bouton qui contient le texte du prono
            page.get_by_text(prono_val, exact=True).first.click()
            
            # 4. Ouvrir le panier et générer le code
            # Ces sélecteurs dépendent de la structure exacte du site au moment T
            page.click(".cart-icon") # Exemple de classe CSS pour le panier
            page.click("#generate-code-button") # Exemple d'ID pour générer le code
            
            # 5. Attendre l'apparition du code-barres et prendre une photo
            barcode_element = page.locator(".barcode-image-class")
            image_path = "barcode.png"
            barcode_element.screenshot(path=image_path)
            
            # Ici, il faudrait normalement uploader l'image vers un service 
            # comme Imgur ou Cloudinary pour avoir une URL publique.
            # Pour l'exemple, on simule l'URL :
            barcode_url = "https://votre-app-railway.app"
            
            browser.close()
            return barcode_url
        except Exception as e:
            browser.close()
            return str(e)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    match = data.get("match")
    prono = data.get("prono")

    if not match or not prono:
        return jsonify({"status": "error", "message": "Données manquantes"}), 400

    # Appel de la fonction de navigation
    result_url = get_sisal_barcode(match, prono)

    if "http" in result_url:
        return jsonify({"status": "success", "barcode_url": result_url})
    else:
        return jsonify({"status": "error", "details": result_url})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
