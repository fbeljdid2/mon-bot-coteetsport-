import os
import asyncio
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright
from playwright_stealth import stealth

app = Flask(__name__)

async def generer_ticket_cote_sport(match_name, pronostic):
    async with async_playwright() as p:
        # Lancement du navigateur (obligatoire avec ces arguments sur Railway)
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        # Masquer le bot pour éviter le blocage du site
        await stealth(page)
        
        try:
            # 1. Aller sur le site officiel
            await page.goto("https://www.coteetsport.ma", wait_until="networkidle")
            
            # 2. Chercher le match (ex: "Real Madrid")
            await page.get_by_placeholder("Rechercher").fill(match_name)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000) # Attendre que les résultats s'affichent
            
            # 3. Cliquer sur le pronostic (1, X, ou 2)
            # On cherche le bouton qui contient exactement ton prono
            await page.get_by_text(pronostic, exact=True).first.click()
            
            # 4. Ouvrir le panier/ticket et Générer le code
            # Note : Ces sélecteurs dépendent de la mise à jour du site
            await page.click(".btn-panier") # Cliquer sur l'icône du panier
            await page.wait_for_timeout(1000)
            
            # Cliquer sur "Générer mon code de réservation"
            await page.get_by_role("button", name="Générer").click()
            
            # 5. Récupérer l'image du Code-Barres
            # On attend que l'image apparaisse à l'écran
            await page.wait_for_selector("img.barcode-img") 
            barcode_url = await page.get_attribute("img.barcode-img", "src")
            
            await browser.close()
            return {"status": "success", "barcode_url": barcode_url}

        except Exception as e:
            await browser.close()
            return {"status": "error", "message": f"Erreur lors de la génération : {str(e)}"}

@app.route('/get-barcode', methods=['POST'])
def get_barcode():
    data = request.json
    # Ton application doit envoyer : {"match": "Nom du Match", "prono": "1"}
    match = data.get('match')
    prono = data.get('prono')
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    resultat = loop.run_until_complete(generer_ticket_cote_sport(match, prono))
    
    return jsonify(resultat)

@app.route('/')
def status():
    return "Bot de réservation en ligne !", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
