import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS  # Important pour Lovable
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async # Pour éviter le blocage

app = Flask(__name__)
CORS(app) # Autorise Lovable à appeler ton bot

async def bot_logic(matchs):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        
        # Appliquer le mode "furtif" pour ne pas être bloqué
        await stealth_async(page)

        try:
            await page.goto("https://www.coteetsport.ma", wait_until="networkidle")
            
            # --- ICI : Ta logique de clic sur les matchs ---
            # Exemple : await page.click(f"text={matchs[0]['nom']}")
            
            # Attendre et récupérer le code-barres
            # Remplace '.le-selecteur-du-code' par le vrai nom du bouton/image
            barcode_element = await page.wait_for_selector(".barcode-image", timeout=20000)
            barcode_url = await barcode_element.get_attribute("src")
            
            await browser.close()
            return {"status": "success", "url": barcode_url}
        except Exception as e:
            await browser.close()
            return {"status": "error", "message": str(e)}

@app.route('/generer-billet', methods=['POST'])
def handle_request():
    data = request.json
    # On lance la boucle asynchrone pour Playwright
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(bot_logic(data.get('matchs', [])))
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
