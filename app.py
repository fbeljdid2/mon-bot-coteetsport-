import os
import logging
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

# Configuration des logs pour voir les erreurs sur Railway
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# --- ROUTE DE SÉCURITÉ POUR RAILWAY (Indispensable) ---
@app.route('/')
@app.route('/health')
def home():
    return "Le bot est en ligne et prêt !", 200

# --- FONCTION PRINCIPALE : NAVIGATION SUR MDJS ---
def get_mdjs_reservation(match_name, prono_val):
    with sync_playwright() as p:
        # Lancement du navigateur (indispensable en mode headless sur Railway)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        try:
            logging.info(f"Tentative pour : {match_name} avec prono {prono_val}")
            
            # 1. Aller sur le site
            page.goto("https://coteetsport.ma", timeout=60000, wait_until="networkidle")
            
            # 2. Simulation de recherche (Exemple simplifié)
            # Note : Le site MDJS utilise souvent des popups, on les ferme si besoin
            if page.locator(".close-modal").is_visible():
                page.click(".close-modal")

            # Ici, le code doit être adapté aux sélecteurs EXACTS du site
            # Pour l'instant, on simule la réussite pour tester la communication
            
            # --- CODE DE GÉNÉRATION ICI ---
            # (C'est ici qu'on ajoute les clics précis sur les boutons du site)
            
            barcode_url = "https://votre-site.com" # Remplacez par l'URL finale
            
            browser.close()
            return {"status": "success", "url": barcode_url}

        except Exception as e:
            logging.error(f"Erreur Playwright : {str(e)}")
            browser.close()
            return {"status": "error", "message": str(e)}

# --- ROUTE APPELÉE PAR LOVABLE / BASE44 ---
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Aucune donnée JSON reçue"}), 400

    match = data.get("match")
    prono = data.get("prono")

    if not match or not prono:
        return jsonify({"status": "error", "message": "Champs 'match' ou 'prono' manquants"}), 400

    # Lancement de la procédure automatisée
    result = get_mdjs_reservation(match, prono)

    if result["status"] == "success":
        return jsonify({
            "status": "success",
            "barcode_url": result["url"]
        })
    else:
        return jsonify({
            "status": "error",
            "details": result["message"]
        }), 500

if __name__ == '__main__':
    # Railway utilise la variable d'environnement PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
