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
    # Simulation d'un vrai navigateur pour éviter d'être bloqué
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/generer-code', methods=['POST'])
def generer_code():
    # On imagine que ton App Lovable envoie {"match": "Real Madrid", "pari": "1"}
    donnees = request.json
    match_nom = donnees.get('match')
    
    driver = None
    try:
        driver = setup_bot()
        wait = WebDriverWait(driver, 20)
        
        # 1. Aller sur le site
        driver.get("https://www.coteetsport.ma")
        time.sleep(5) # Attente du chargement complet

        # 2. Chercher le match (Exemple simplifié : on clique sur la première cote disponible)
        # Note: Dans la réalité, il faudrait chercher 'match_nom' dans la page
        bouton_cote = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".odd-button")))
        bouton_cote.click()
        time.sleep(2)

        # 3. Ouvrir le panier et cliquer sur "Générer code de réservation"
        # Ces sélecteurs (ID/Classe) sont des exemples, ils doivent correspondre au site
        bouton_panier = wait.until(EC.element_to_be_clickable((By.ID, "booking-button")))
        bouton_panier.click()
        
        # 4. Récupérer le texte du code de réservation (ex: "A12B34")
        code_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "booking-code-value")))
        code_final = code_element.text

        # 5. Récupérer l'image du QR Code / Code-barres
        qr_code_url = driver.find_element(By.ID, "barcode-img").get_attribute("src")

        return jsonify({
            "success": True, 
            "code_reservation": code_final,
            "image_url": qr_code_url
        })

    except Exception as e:
        return jsonify({"success": False, "erreur": str(e)})
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
