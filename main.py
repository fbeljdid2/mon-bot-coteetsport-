import os
import time
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

def setup_bot():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Simulation d'un vrai utilisateur
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/')
def home():
    return "Bot Said MDJS en ligne ! Prêt pour le test."

@app.route('/tester-remplissage')
def tester_remplissage():
    driver = None
    try:
        driver = setup_bot()
        wait = WebDriverWait(driver, 25)
        
        # 1. Aller sur le site
        driver.get("https://www.coteetsport.ma")
        time.sleep(10) # On attend bien que le site charge (Sisal est lent)

        # 2. Chercher les boutons de cotes
        # On cherche les éléments qui permettent de parier
        cotes = driver.find_elements(By.CSS_SELECTOR, ".button-selection, .odd-button, [class*='selection']")
        
        if len(cotes) > 0:
            # ON CLIQUE SUR LA PREMIÈRE COTE TROUVÉE
            cotes[0].click() 
            time.sleep(3)
            
            return jsonify({
                "success": True, 
                "message": "Bravo Said ! Le bot a cliqué sur la première cote du site."
            })
        else:
            # Si on ne trouve pas de bouton, on prend une photo de l'écran pour comprendre
            driver.save_screenshot("erreur.png")
            return jsonify({"success": False, "erreur": "Aucun bouton de pari trouvé sur la page."})

    except Exception as e:
        return jsonify({"success": False, "erreur": str(e)})
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
