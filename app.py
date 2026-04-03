import os
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

def generate_barcode_logic(match, prono, mise):
    with sync_playwright() as p:
        # Configuration spécifique pour éviter les crashs sur serveur
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Navigation vers le site
            page.goto("https://coteetsport.ma", wait_until="networkidle", timeout=60000)
            
            # --- AJOUTEZ ICI VOS CLICS ET REMPLISSAGE DE PANIER ---
            # Pour le test, on simule une URL de retour
            barcode_url = "https://coteetsport.ma/images/barcode_placeholder.png"
            
            browser.close()
            return barcode_url
        except Exception as e:
            print(f"Erreur Playwright: {e}")
            browser.close()
            return None

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "JSON vide"}), 400

    match = data.get("match")
    prono = data.get("prono")
    mise = data.get("mise")

    url = generate_barcode_logic(match, prono, mise)

    if url:
        return jsonify({"status": "success", "barcode_url": url})
    return jsonify({"status": "error", "message": "Echec generation"}), 500

if __name__ == '__main__':
    # Railway impose d'écouter sur 0.0.0.0 et sur le port fourni par l'environnement
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
