import os
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

def setup_browser():
    chrome_options = Options()
    # Configuration obligatoire pour Railway (serveur sans écran)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Pour éviter d'être bloqué comme un robot
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    # Sur Railway avec Docker, le chemin de chromium est /usr/bin/chromium
    chrome_options.binary_location = "/usr/bin/chromium"
    
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

@app.route('/')
def home():
    return "🚀 Le bot de Said pour Cote&Sport est en ligne !"

@app.route('/test-clic')
def test_clic():
    driver = None
    try:
        driver = setup_browser()
        # 1. Aller sur le site officiel
        driver.get("https://www.coteetsport.ma")
        
        # 2. Attendre que la page charge (max 10 secondes)
        wait = WebDriverWait(driver, 10)
        
        # 3. Essayer de trouver un élément pour prouver que le bot "voit" la page
        # On cherche par exemple le titre ou un bouton du menu
        page_title = driver.title
        
        driver.quit()
        return jsonify({
            "statut": "Succès",
            "message": "Le bot a réussi à ouvrir le site MDJS !",
            "titre_page": page_title
        })
        
    except Exception as e:
        if driver:
            driver.quit()
        return jsonify({
            "statut": "Erreur",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    # Railway utilise la variable d'environnement PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
