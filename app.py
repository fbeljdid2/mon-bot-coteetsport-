from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import uuid

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Bot actif"

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        match = data.get("match")
        prono = data.get("prono")
        mise = data.get("mise")

        if not match or not prono or not mise:
            return jsonify({"status": "error", "message": "Données manquantes"}), 400

        # CONFIG CHROME (important pour Railway)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        # 1️⃣ Ouvrir le site
        driver.get("https://coteetsport.ma/")
        time.sleep(5)

        # ⚠️ ICI TU DOIS ADAPTER SELON LE SITE
        # Exemple logique (à adapter avec inspect élément)

        # 2️⃣ Chercher match
        # driver.find_element(By.XPATH, "...").click()

        # 3️⃣ Choisir prono
        # driver.find_element(By.XPATH, "...").click()

        # 4️⃣ Ajouter au panier
        # driver.find_element(By.XPATH, "...").click()

        # 5️⃣ Mettre mise
        # driver.find_element(By.XPATH, "...").send_keys(mise)

        # 6️⃣ Générer ticket
        # driver.find_element(By.XPATH, "...").click()

        time.sleep(5)

        # 7️⃣ Screenshot
        filename = f"{uuid.uuid4()}.png"
        filepath = f"/tmp/{filename}"
        driver.save_screenshot(filepath)

        driver.quit()

        # 8️⃣ URL publique (Railway ne sert pas fichiers → solution simple)
        return jsonify({
            "status": "success",
            "barcode_url": "data:image/png;base64," + encode_image(filepath)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def encode_image(path):
    import base64
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
