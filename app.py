from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)

def generate_barcode_logic(match, prono, mise):
    with sync_playwright() as p:
        # Lancement du navigateur avec options de sécurité assouplies
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        
        # Le contexte ignore les erreurs HTTPS/SSL comme suggéré par l'IA
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            # Navigation vers le site (en HTTP si le HTTPS bloque)
            page.goto("http://coteetsport.ma", wait_until="networkidle", timeout=60000)

            # --- INSÉREZ ICI VOTRE LOGIQUE PLAYWRIGHT SPÉCIFIQUE ---
            # Exemple : page.fill("#input_match", match), etc.
            # Cette partie dépend de la structure exacte du site sisal.
            
            # Simulation d'une URL de résultat pour l'exemple
            # Dans votre code réel, récupérez l'URL du code-barres généré
            barcode_url = "https://votre-stockage.com" 
            
            browser.close()
            return barcode_url
        except Exception as e:
            browser.close()
            print(f"Erreur Playwright: {e}")
            return None

@app.route('/predict', methods=['POST'])
def predict():
    # Récupération des données envoyées par Lovable
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "Aucune donnée reçue"}), 400

    match = data.get("match")
    prono = data.get("prono")
    mise = data.get("mise")

    # Appel de la fonction de génération
    url_resultat = generate_barcode_logic(match, prono, mise)

    if url_resultat:
        return jsonify({
            "status": "success",
            "barcode_url": url_resultat
        })
    else:
        return jsonify({
            "status": "error", 
            "message": "Erreur lors de la génération du code-barres"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
