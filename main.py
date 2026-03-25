import os
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = FastAPI()

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Pas d'interface graphique
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # On précise le chemin de Chrome pour Railway
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

@app.get("/")
def home():
    return {"status": "Bot Cote&Sport prêt pour l'action !"}

@app.get("/test-clic")
def test_clic():
    driver = get_driver()
    try:
        # 1. Aller sur le site
        driver.get("https://www.coteetsport.ma")
        
        # 2. Attendre que le bouton "Accepter les cookies" apparaisse et cliquer
        wait = WebDriverWait(driver, 10)
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            cookie_btn.click()
            resultat = "Cookies acceptés. "
        except:
            resultat = "Pas de bouton cookies trouvé. "

        # 3. Prendre le titre de la page pour vérifier
        resultat += f"Titre de la page : {driver.title}"
        
        return {"success": True, "details": resultat}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        driver.quit()
