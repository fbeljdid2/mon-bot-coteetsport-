import os
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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
    # Cette ligne est magique pour éviter les erreurs sur Railway
    options.add_argument("--remote-debugging-port=9222") 
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.coteetsport.ma")
        titre = driver.title
        driver.quit()
        return {"success": True, "site": "Cote & Sport", "titre_page": titre}
    except Exception as e:
        return {"success": False, "erreur": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
