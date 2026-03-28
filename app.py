import os
import asyncio
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright
from playwright_stealth import stealth

app = Flask(__name__)

async def automate_bet(match_name, market_type, prediction):
    """
    market_type: '1X2', 'Plus/Moins', 'But/Sans But'
    prediction: '1', 'X', '2', '+2.5', 'But', etc.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        await stealth(page)
        
        try:
            # 1. Accès au site
            await page.goto("https://www.coteetsport.ma/", wait_until="networkidle")
            
            # 2. Recherche du match
            await page.get_by_placeholder("Rechercher").fill(match_name)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)
            
            # 3. Sélection du type de pari (Marché)
            # On clique sur l'onglet correspondant (ex: "Plus/Moins")
            if market_type != "1X2":
                await page.get_by_text(market_type, exact=False).click()
            
            # 4. Sélection de la prédiction
            # On cherche le texte de la cote associée à la prédiction
            await page.get_by_text(prediction, exact=True).click()
            
            # 5. Génération du Code-Barres
            # Note: Le bouton "Panier" ou "Générer" doit être cliqué
            await page.click(".btn-generate-code") # Sélecteur à adapter selon le DOM réel
            await page.wait_for_selector("img.barcode")
            
            # Récupération de l'image du code-barres
            barcode_src = await page.get_attribute("img.barcode", "src")
            
            await browser.close()
            return {"status": "success", "barcode": barcode_src}

        except Exception as e:
            await browser.close()
            return {"status": "error", "message": str(e)}

@app.route('/bet', methods=['POST'])
def handle_bet():
    data = request.json
    # Format attendu: {"match": "Maroc vs Espagne", "type": "Plus/Moins", "pari": "+2.5"}
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(automate_bet(data['match'], data['type'], data['pari']))
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
