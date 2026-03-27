import os
import asyncio
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright

app = Flask(__name__)

# Route pour recevoir les données de Lovable
@app.route('/generer-billet', methods=['POST'])
async def generer_billet():
    # 1. Récupération des données envoyées par Lovable
    # Format attendu : {"matchs": [{"equipe": "Real Madrid", "pronostic": "1"}, ...]}
    data = request.json
    matchs = data.get('matchs', [])
    
    if not matchs:
        return jsonify({"erreur": "Aucun match reçu"}), 400

    async with async_playwright() as p:
        # Lancement du navigateur (indispensable pour Railway)
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()

        try:
            # 2. Navigation vers le site officiel MDJS
            await page.goto("https://www.coteetsport.ma", timeout=60000)
            
            # --- LOGIQUE DE REMPLISSAGE DU PANIER ---
            # Pour chaque match reçu, le bot doit cliquer sur les bonnes cotes.
            # Exemple simplifié (à adapter selon les sélecteurs précis du site) :
            for match in matchs:
                # On cherche le match par son nom sur la page
                # await page.get_by_text(match['equipe']).click()
                pass 
            
            # 3. Cliquer sur le bouton "Générer code de réservation"
            # await page.click("#bouton-reserver") 
            
            # 4. Capturer le code-barres (Image ou URL)
            # On attend que l'élément apparaisse
            barcode_element = await page.wait_for_selector(".barcode-image-selector", timeout=10000)
            barcode_url = await barcode_element.get_attribute("src")
            
            await browser.close()
            
            # Renvoi du résultat à Lovable
            return jsonify({
                "statut": "success",
                "barcode_url": barcode_url
            })

        except Exception as e:
            await browser.close()
            return jsonify({"statut": "erreur", "message": str(e)}), 500

if __name__ == "__main__":
    # Railway utilise dynamiquement le port défini dans ses variables d'environnement
    port = int(os.environ.get("PORT", 8080))
    # Utilisation d'un serveur compatible avec l'asynchrone (pour Playwright)
    app.run(host='0.0.0.0', port=port)
