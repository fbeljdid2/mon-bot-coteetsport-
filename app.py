import os
import asyncio
from flask import Flask
from playwright.async_api import async_playwright
# CORRECTION : On importe 'stealth' et non 'stealth_async'
from playwright_stealth import stealth

app = Flask(__name__)

async def run_bot():
    async with async_playwright() as p:
        # Configuration pour Railway (no-sandbox est obligatoire)
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.new_page()
        
        # CORRECTION : Utilisation de la fonction stealth universelle
        await stealth(page)
        
        # REMPLACER l'URL ci-dessous par celle de votre site de sport
        await page.goto("https://www.google.com")
        print(f"Connecté à : {await page.title()}")
        await browser.close()

@app.route('/')
def health_check():
    return "Bot en cours d'exécution", 200

if __name__ == "__main__":
    # Récupération du port dynamique de Railway
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
