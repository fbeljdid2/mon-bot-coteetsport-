import os
import time
from flask import Flask, jsonify, request
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
    # Ce "User-Agent" est crucial pour que le site MDJS ne bloque pas ton bot
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/generer-code', methods=['POST'])
def generer_code():
    # Ton appli Lovable enverra par exemple : {"match_index": 0} 
    # (le 1er match de la liste)
    driver = None
    try:
        driver = setup_bot()
        wait = WebDriverWait(driver, 20) # On attend 20 secondes max
        
        # 1. Aller sur le site
        driver.get("https://www.coteetsport.ma")
        time.sleep(5) # On laisse le temps aux matchs de s'afficher

        # 2. CLIQUER SUR LA PREMIÈRE COTE DISPONIBLE (Test)
        # On cherche les boutons qui contiennent les cotes (classe 'odd-button' sur Sisal)
        boutons_cotes = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "odd-button")))
        boutons_cotes[0].click() # Clique sur la toute première cote
        print("Cote sélectionnée !")
        time.sleep(2)

        # 3. CLIQUER SUR LE PANIER / RÉSERVATION
        # Sur le site Sisal, le bouton de réservation a souvent la classe 'booking-button'
        bouton_reserver = wait.until(EC.element_to_be_clickable((By.ID, "book-button")))
        bouton_reserver.click()
        print("Panier ouvert !")

        # 4. RÉCUPÉRER LE CODE ET L'IMAGE
        # On attend que le code de réservation apparaisse à l'écran
        code_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "booking-code")))
        code_final = code_element.text
        
        # On cherche l'image du code-barres (QR Code)
        image_element = driver.find_element(By.TAG_NAME, "img") # À affiner selon le site
        url_barcode = image_element.get_attribute("src")

        return jsonify({
            "success": True, 
            "code": code_final,
            "barcode_url": url_barcode
        })

    except Exception as e:
        return jsonify({"success": False, "erreur": str(e)})
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
