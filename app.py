import os
import asyncio
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright
from playwright_stealth import stealth

app = Flask(__name__)

async def bot_cote_et_sport(match_name, prediction):
    async with async_playwright() as p:
        # Lancement avec les options de sécurité pour Railway
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        # Masquer le bot (Anti-bot bypass)
        await stealth(page)
        
        try:
            # 1. Aller sur le site
            await page.goto("https://www.coteetsport.ma", wait_until="networkidle")
            
            # 2. Logique de recherche (Exemple simplifié)
            # Vous devrez adapter les sélecteurs CSS (.class ou #id) selon le site
            await page.fill('input[placeholder="Rechercher"]', match_name)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2000)
            
            # 3. Cliquer sur la prédiction (1, X, ou 2)
            # Ici, il faudra identifier le bouton précis du match
            await page.click(f"text={prediction}")
            
            # 4. Générer le Code-Barres
            await page.click("button:has-text('Générer mon code')")
            await page.wait_for_selector(".barcode-image") # Attendre l'image du code
            
            # 5. Récupérer l'URL de l'image ou faire une capture
            barcode_url = await page.get_attribute(".barcode-image", "src")
            
            await browser.close()
            return barcode_url
        except Exception as e:
            await browser.close()
            return f"Erreur : {str(e)}"

@app.route('/generate-bet', methods=['POST'])
def generate_bet():
    data = request.json
    match = data.get('match')
    prediction = data.get('prediction')
    
    # Lancement du bot en arrière-plan
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    barcode = loop.run_until_complete(bot_cote_et_sport(match, prediction))
    
    return jsonify({"barcode_url": barcode})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
