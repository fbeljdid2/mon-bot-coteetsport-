from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

app = Flask(__name__)

# Identifiants depuis variables Railway (sécurisé)
EMAIL = os.getenv('EMAIL', 'votre@email.com')
PASSWORD = os.getenv('PASSWORD', 'votremotdepasse')

@app.route('/')
def home():
    return "Bot prêt pour générer code-barres SISAL !"

@app.route('/test-clic')
def test_clic():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://www.coteetsport.ma')
    time.sleep(3)
    title = driver.title
    driver.quit()
    return f"✅ Selenium OK ! Titre site: {title}"

@app.route('/generer-barcode', methods=['POST'])
def generer_barcode():
    try:
        data = request.get_json()  # Prédictions: [{"match": "PSG-Real", "cote": "2.5"}]
        if not data:
            return jsonify({"erreur": "Aucune prédiction envoyée"}), 400
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Étape 1: Login
        driver.get('https://www.coteetsport.ma')
        time.sleep(2)
        # Cliquez bouton Connexion (adaptez XPath F12)
        driver.find_element(By.XPATH, '//a[contains(text(), "Connexion") or contains(text(), "Login")]').click()
        time.sleep(2)
        driver.find_element(By.NAME, 'email').send_keys(EMAIL)  # Ou 'username'
        driver.find_element(By.NAME, 'password').send_keys(PASSWORD)
        driver.find_element(By.XPATH, '//button[@type="submit" or contains(text(), "Connexion")]').click()
        time.sleep(5)
        
        # Étape 2: Football
        driver.get('https://www.coteetsport.ma/cote-sport/sport/football')
        time.sleep(5)
        
        # Étape 3: Ajouter paris
        panier_items = []
        for pred in data:
            # Exemple XPath - inspectez site pour exact (F12 > chercher match)
            xpath_match = f"//span[contains(text(), '{pred['match']}')]"
            match_elem = driver.find_element(By.XPATH, xpath_match)
            # Clique cote proche
            cote_btn = match_elem.find_element(By.XPATH, ".//following::button[contains(@class, 'odd') or @data-odds][1]")
            cote_btn.click()
            panier_items.append(pred['match'])
            time.sleep(2)
        
        # Étape 4: Panier + code-barres
        driver.find_element(By.XPATH, '//a[contains(text(), "Panier")]').click()
        time.sleep(3)
        # Confirmez/Validez (adaptez)
        driver.find_element(By.XPATH, '//button[contains(text(), "Valider") or contains(text(), "Générer")]').click()
        time.sleep(5)
        
        # Extraire barcode (img ou code text)
        barcode_elem = driver.find_element(By.TAG_NAME, 'img')  # Ou By.CLASS_NAME 'barcode'
        barcode_src = barcode_elem.get_attribute('src')
        
        driver.quit()
        return jsonify({
            "status": "succès",
            "barcode_url": barcode_src,
            "prédictions_ajoutées": panier_items
        })
    
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return jsonify({"erreur": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
