import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

app = Flask(__name__)
CORS(app)

async def bot_logic(matchs_data):
    async with async_playwright() as p:
        # Lancement avec paramètres pour éviter les blocages sur Railway
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        await stealth_async(page)

        try:
            # 1. Aller sur la page Foot de la MDJS
            await page.goto("https://www.coteetsport.ma", wait_until="networkidle", timeout=60000)
            
            for match in matchs_data:
                equipe = match.get('equipe')  # ex: "Real Madrid"
                pronostic = match.get('prono') # ex: "1", "N" ou "2"

                # 2. Chercher le match par son nom à l'écran
                # On utilise une recherche floue pour plus de sécurité
                match_row = page.locator(f"xpath=//div[contains(text(), '{equipe}')]/ancestor::div[contains(@class, 'event-row')]")
                
                if await match_row.count() > 0:
                    # 3. Cliquer sur la cote (1, N ou 2) à l'intérieur de la ligne du match
                    # Les sélecteurs MDJS sont souvent des index : 1er bouton=1, 2eme=N, 3eme=2
                    index = 0 if pronostic == "1" else (1 if pronostic == "N" else 2)
                    boutons_cotes = match_row.locator(".outcome-button") # Vérifier ce sélecteur sur le site
                    await boutons_cotes.nth(index).click()
                    await asyncio.sleep(0.5) # Pause pour simuler un humain

            # 4. Ouvrir le panier et générer le code
            await page.click(".shopping-cart-icon") # Sélecteur du panier
            await page.click("#generate-qr-btn")    # Bouton "Générer QR"
            
            # 5. Attendre l'image du QR Code / Code-barres
            barcode_element = await page.wait_for_selector("img.qr-code-result", timeout=15000)
            barcode_url = await barcode_element.get_attribute("src")
            
            await browser.close()
            return {"status": "success", "url": barcode_url}

        except Exception as e:
            await browser.close()
            return {"status": "error", "message": f"Erreur bot: {str(e)}"}

@app.route('/generer-billet', methods=['POST'])
def handle_request():
    data = request.json
    matchs = data.get('matchs', [])
    
    # Exécution de la boucle asynchrone
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(bot_logic(matchs))
    finally:
        loop.close()
        
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
