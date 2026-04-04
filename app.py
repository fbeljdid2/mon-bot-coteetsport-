import os
import logging
import time
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

MDJS_EMAIL = os.environ.get("MDJS_EMAIL", "")
MDJS_PASSWORD = os.environ.get("MDJS_PASSWORD", "")

@app.route('/')
@app.route('/health')
def home():
    return "Le bot MDJS est en ligne et prêt !", 200

def screenshot_b64(page):
    try:
        return "data:image/png;base64," + base64.b64encode(page.screenshot(full_page=False)).decode()
    except:
        return ""

def get_mdjs_reservation(match_name, prono_val, mise_val):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            logging.info("Étape 1 : Login...")
            page.goto("https://zonereservee.coteetsport.ma/login/", timeout=60000, wait_until="domcontentloaded")
            time.sleep(2)

            page.fill("input[type='email'], input[name='email'], #email", MDJS_EMAIL)
            page.fill("input[type='password'], input[name='password'], #password", MDJS_PASSWORD)
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)

            if "login" in page.url:
                logging.error("Login échoué")
                return {"status": "error", "message": "Login échoué. Vérifiez MDJS_EMAIL/MDJS_PASSWORD.", "screenshot": screenshot_b64(page)}

            logging.info(f"Login OK - URL: {page.url}")

            page.goto("https://www.coteetsport.ma/cote-sport", timeout=60000, wait_until="domcontentloaded")
            time.sleep(3)

            try:
                page.click(".close, .btn-close, [aria-label='Close']", timeout=3000)
            except:
                pass

            logging.info(f"Étape 3 : Recherche match '{match_name}', prono '{prono_val}'...")
            team1 = match_name.split(" vs ")[0].strip()

            try:
                match_row = page.locator(f"tr:has-text('{team1}'), .bet-row:has-text('{team1}'), [class*='event']:has-text('{team1}')").first
                if prono_val == "1":
                    match_row.locator("td:nth-child(1) button, .outcome-1, [data-selection='1']").first.click(timeout=5000)
                elif prono_val == "X":
                    match_row.locator("td:nth-child(2) button, .outcome-x, [data-selection='X']").first.click(timeout=5000)
                elif prono_val == "2":
                    match_row.locator("td:nth-child(3) button, .outcome-2, [data-selection='2']").first.click(timeout=5000)
                logging.info(f"Cote '{prono_val}' cliquée")
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Sélection cote échouée: {e}")
                try:
                    page.locator(f"td[data-bet='{prono_val}'], button[data-bet='{prono_val}']").first.click(timeout=5000)
                except:
                    pass

            logging.info("Étape 4 : Saisie de la mise...")
            try:
                stake_input = page.locator("input[class*='stake'], input[placeholder*='Mise'], input[placeholder*='mise'], .ticket-input input, #mise, input[type='number']").first
                stake_input.wait_for(timeout=8000)
                stake_input.triple_click()
                stake_input.fill(str(mise_val))
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Champ mise non trouvé: {e}")

            logging.info("Étape 5 : Clic sur Réserver...")
            try:
                reserver_btn = page.locator("button:has-text('Réserver'), button:has-text('RÉSERVER'), a:has-text('Réserver')").first
                reserver_btn.wait_for(timeout=8000)
                reserver_btn.click()
                page.wait_for_load_state("networkidle", timeout=30000)
                time.sleep(5)
            except Exception as e:
                logging.warning(f"Bouton Réserver non trouvé: {e}")

            logging.info("Étape 6 : Capture du code barres...")
            logging.info(f"URL après réservation: {page.url}")

            barcode_url = ""
            images = page.query_selector_all("img")
            for img in images:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                logging.info(f"Image - src: {src[:80]}, alt: {alt}")
                if any(k in src.lower() for k in ["barcode", "qr", "code", "ticket", "reservation", "recu"]):
                    barcode_url = src if src.startswith("http") else "https://www.coteetsport.ma" + src
                    logging.info(f"Barcode trouvé: {barcode_url}")
                    break

            if not barcode_url:
                canvas = page.query_selector("canvas")
                if canvas:
                    barcode_url = page.evaluate("() => document.querySelector('canvas').toDataURL('image/png')")
                    logging.info("Barcode capturé depuis canvas")

            if not barcode_url:
                logging.warning("Aucune image barcode, screenshot de la page")
                barcode_url = screenshot_b64(page)

            res_code = ""
            for selector in [".reservation-code", ".booking-id", ".ticket-code", ".code-reservation", "[class*='confirmation']"]:
                try:
                    el = page.query_selector(selector)
                    if el:
                        res_code = el.inner_text().strip()
                        break
                except:
                    continue

            browser.close()
            return {"status": "success", "code": res_code, "barcode_url": barcode_url}

        except Exception as e:
            logging.error(f"Erreur générale: {str(e)}")
            sc = screenshot_b64(page)
            browser.close()
            return {"status": "error", "message": str(e), "screenshot": sc}


@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Données JSON manquantes"}), 400

    match = data.get("match")
    prono = data.get("prono")
    mise = data.get("mise", "10")

    if not match or not prono:
        return jsonify({"status": "error", "message": "Champs 'match' ou 'prono' manquants"}), 400

    if not MDJS_EMAIL or not MDJS_PASSWORD:
        return jsonify({"status": "error", "message": "Variables MDJS_EMAIL et MDJS_PASSWORD non configurées"}), 500

    result = get_mdjs_reservation(match, prono, mise)

    if result["status"] == "success":
        return jsonify({
            "status": "success",
            "reservation_code": result["code"],
            "barcode_url": result["barcode_url"]
        })
    else:
        return jsonify({
            "status": "error",
            "details": result["message"],
            "screenshot": result.get("screenshot", "")
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
