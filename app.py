from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

app = Flask(__name__)

@app.route('/generer-code', methods=['POST'])
def generer_code():
    # On récupère les numéros de matchs envoyés par Lovable
    donnees = request.json
    matchs = donnees.get('matchs', []) # Exemple: [101, 205]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        stealth_sync(page) # Pour ne pas être détecté comme un robot

        # 1. Aller sur le site
        page.goto("https://www.coteetsport.ma")

        # 2. Ici le bot cherche et clique sur tes matchs
        for m in matchs:
            # On cherche le match par son numéro et on clique sur "Gagner" (1)
            page.click(f"text={m}") 
            # Note: C'est ici qu'il faudra ajuster selon le design du site

        # 3. Cliquer sur le panier pour générer le code
        page.click(".btn-generate-qr") # Nom du bouton à vérifier sur le site

        # 4. Prendre une photo du code-barres
        screenshot_path = "code_barres.png"
        page.locator("#qr-code-zone").screenshot(path=screenshot_path)

        browser.close()
        return jsonify({"status": "Succès", "image_url": "Lien_vers_l_image"})

@app.route('/')
def home():
    return "🚀 Bot de Said prêt à cliquer !"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
