from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot en ligne avec Selenium !"

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
    return f"Site chargé ! Titre: {title}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
