import os
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

def generate_barcode_logic(match, prono, mise):
    """Logique pour naviguer sur le site et récupérer le code-barres."""
    with sync_playwright() as p:
        # Lancement du navigateur avec options de compatibilité pour Railway
        browser = p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        # Ignorer les erreurs HTTPS/SSL du site cible
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            # Navigation vers le site officiel
            # On utilise un timeout de 60s car le site peut être lent
            page.goto("https://coteetsport.ma", wait_until="networkidle", timeout=60000)

            # --- VOS ÉTAPES PLAYWRIGHT ICI ---
            # Exemple : page.click(".nom-du-bouton")
            # Pour l'instant, on simule le succès pour tester la connexion
            
            # Remplacez cette URL par celle que vous extrayez du site
            barcode_url = "https://coteetsport.ma" 
            
            browser.close()
            return barcode_url
        except Exception as e:
            print(f"Erreur lors de la navigation : {e}")
            browser.close()
            return None

@app.route('/predict', methods=['POST'])
def predict():
    # Récupération du JSON envoyé par Lovable
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "Données JSON manquantes"}), 400

    match = data.get("match")
    prono = data.get("prono")
    mise = data.get("mise")

    # Génération du code-barres via Playwright
    result_url = generate_barcode_logic(match, prono, mise)

    if result_url:
        return jsonify({
            "status": "success",
            "barcode_url": result_url
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Le bot n'a pas pu générer le code-barres"
        }), 500

if __name__ == '__main__':
    # Railway utilise la variable d'environnement PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
