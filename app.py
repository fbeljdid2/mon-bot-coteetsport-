import os
import asyncio
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright
from playwright_stealth import stealth

app = Flask(__name__)

# Cette fonction contient la logique pour aller sur coteetsport.ma
async def automate_bet(match_name, prediction):
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.new_page()
        await stealth(page)
        
        try:
            await page.goto("https://www.coteetsport.ma", wait_until="networkidle")
            # --- ICI : Ajoute ta logique de clic sur le match et la mise ---
            # Exemple : await page.fill('#search', match_name)
            
            # Simulation d'un résultat (remplace par la capture du code-barres)
            result_message = f"Pari placé pour {match_name} avec prédiction {prediction}"
            await browser.close()
            return {"status": "success", "message": result_message}
        except Exception as e:
            await browser.close()
            return {"status": "error", "message": str(e)}

# C'est l'URL que ton application va contacter
@app.route('/receive-match', methods=['POST'])
def receive_match():
    data = request.json # Ton application envoie les infos ici
    match = data.get('match')
    prediction = data.get('prediction')

    if not match or not prediction:
        return jsonify({"error": "Données manquantes"}), 400

    # Lancement de l'automatisation
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(automate_bet(match, prediction))

    return jsonify(response)

@app.route('/')
def health():
    return "Bot actif et prêt !", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
