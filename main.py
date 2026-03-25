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
    # On imite un vrai utilisateur pour ne pas être bloqué
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/')
def home():
    return "Bot Said MDJS en ligne !"

@app.route('/tester-remplissage')
def tester_remplissage():
    driver = None
    try:
        driver = setup_bot()
        wait = WebDriverWait(driver, 20)
        
        # 1. Aller sur le site
        driver.get("https://www.coteetsport.ma")
        time.sleep(7) # On attend que tout charge bien

        # 2. On cherche un bouton qui contient le mot "FOOTBALL" et on clique
        try:
            btn_foot = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'FOOTBALL')]")))
            btn_foot.click()
            time.sleep(3)
        except:
            print("Bouton Football non trouvé, on continue...")

        # 3. On cherche les boutons de cotes (souvent des éléments avec une classe de type 'selection')
        # On va essayer de cliquer sur le premier bouton qui ressemble à une cote
        cotes = driver.find_elements(By.CSS_SELECTOR, "[class*='selection'], [class*='odd']")
        if len(cotes) > 0:
            cotes[0].click() # On clique sur la 1ère cote
            time.sleep(2)
            
            # 4. On cherche le bouton "RÉSERVER" ou l'icône du panier
            # Sur Sisal, c'est souvent un bouton en bas ou à droite
            return jsonify({
                "success": True, 
                "message": "Le bot a cliqué sur une cote ! Le panier devrait être rempli."
            })
        else:
            return jsonify({"success": False, "erreur": "Aucune cote trouvée sur la page."})

    except Exception as e:
        return jsonify({"success": False, "erreur": str(e)})
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
