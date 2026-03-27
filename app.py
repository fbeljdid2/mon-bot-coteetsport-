import os
import asyncio
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright

app = Flask(__name__)

# Fonction pour gérer la logique du navigateur
async def run_browser_logic(matchs):
    async with async_playwright() as p:
        # Configuration spécifique pour Railway (headless=True est obligatoire)
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()

        try:
            # 1. Aller sur le site
            await page.goto("https://www.coteetsport.ma", wait_until="networkidle")
            
            # 2. Logique de remplissage (Exemple de clic par sélecteur)
            for m in matchs:
                # IMPORTANT : Tu dois trouver le sélecteur exact du bouton de cote
                # Exemple : cliquer sur la cote '1' du match avec l'ID envoyé par Lovable
                # selector = f"div[data-match-id='{m['id']}'] .outcome-1"
                # await page.click(selector)
                pass

            # 3. Cliquer sur le bouton de réservation (à adapter au vrai ID du bouton)
            await page.click("#btn-generate-qr") 
            
            # 4. Attendre le code-barres et prendre une photo ou l'URL
            barcode_element = await page.wait_for_selector("#qr-code-img")
            barcode_url = await barcode_element.get_attribute("src")
            
            await browser.close()
            return {"statut": "success", "barcode_url": barcode_url}

        except Exception as e:
            await browser.close()
            return {"statut": "erreur", "message": str(e)}

@app.route('/generer-billet', methods=['POST'])
def generer_billet():
    data = request.json
    matchs = data.get('matchs', [])
    
    # Exécuter la logique asynchrone dans Flask
    resultat = asyncio.run(run_browser_logic(matchs))
    
    return jsonify(resultat)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
