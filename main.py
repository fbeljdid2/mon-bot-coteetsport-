import os
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Le bot est en ligne !"}

@app.get("/test-clic")
def test_clic():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Cette ligne installe automatiquement le bon driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("https://www.coteetsport.ma")
        titre = driver.title
        driver.quit()
        
        return {"success": True, "site": "MDJS", "titre": titre}
    except Exception as e:
        return {"success": False, "erreur": str(e)}
