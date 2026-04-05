from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os
import base64
import time
import traceback

app = Flask(__name__)

MDJS_EMAIL = os.environ.get("MDJS_EMAIL", "")
MDJS_PASSWORD = os.environ.get("MDJS_PASSWORD", "")

def try_fill(page, selectors, value):
    for sel in selectors:
        try:
            if page.locator(sel).count() > 0:
                page.fill(sel, value)
                return True
        except:
            continue
    return False

def try_click(page, selectors):
    for sel in selectors:
        try:
            if page.locator(sel).count() > 0:
                page.click(sel)
                return True
        except:
            continue
    return False

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    match = data.get("match", "")
    prono = data.get("prono", "")
    mise = data.get("mise", "10")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 1. Login
            page.goto("https://zonereservee.coteetsport.ma/login", timeout=60000, wait_until="domcontentloaded")
            time.sleep(3)

            try:
                page.wait_for_selector("input[type='email'], input[name='email'], input[name='username'], #email", timeout=10000)
            except:
                pass

            try_fill(page, ["input[type='email']", "input[name='email']", "input[name='username']", "#email", "#username"], MDJS_EMAIL)
            try_fill(page, ["input[type='password']", "input[name='password']", "#password"], MDJS_PASSWORD)
            try_click(page, ["button[type='submit']", "input[type='submit']", "button:has-text('Connexion')", "button:has-text('Se connecter')", ".btn-login", ".login-btn"])

            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)

            current_url = page.url
            login_screenshot = page.screenshot()

            if "login" in current_url or "signin" in current_url:
                b64 = base64.b64encode(login_screenshot).decode("utf-8")
                browser.close()
                return jsonify({
                    "status": "error",
                    "message": f"Echec connexion. URL: {current_url}. Verifiez MDJS_EMAIL et MDJS_PASSWORD.",
                    "debug_screenshot": f"data:image/png;base64,{b64}"
                }), 400

            # 2. Naviguer vers la grille/ticket
            ticket_pages = [
                "https://zonereservee.coteetsport.ma/",
                "https://zonereservee.coteetsport.ma/grille",
                "https://zonereservee.coteetsport.ma/ticket",
                "https://zonereservee.coteetsport.ma/reservation",
            ]
            for url in ticket_pages:
                try:
                    page.goto(url, timeout=20000, wait_until="domcontentloaded")
                    time.sleep(2)
                    break
                except:
                    continue

            # 3. Screenshot de la page après navigation
            full_screenshot = page.screenshot(full_page=True)
            b64 = base64.b64encode(full_screenshot).decode("utf-8")
            barcode_url = f"data:image/png;base64,{b64}"

            # 4. Chercher un vrai code barres sur la page
            barcode_selectors = [
                "img.barcode", "img[alt*='barcode']", "img[alt*='code']", "img[alt*='barre']",
                ".barcode img", ".code-barre img", "canvas.barcode",
                "img[src*='barcode']", "img[src*='qr']", ".ticket img", ".reservation img"
            ]
            for sel in barcode_selectors:
                try:
                    if page.locator(sel).count() > 0:
                        el = page.locator(sel).first
                        el_screenshot = el.screenshot()
                        if len(el_screenshot) > 500:
                            b64 = base64.b64encode(el_screenshot).decode("utf-8")
                            barcode_url = f"data:image/png;base64,{b64}"
                            break
                except:
                    continue

            final_url = page.url
            browser.close()

        return jsonify({
            "status": "success",
            "barcode_url": barcode_url,
            "page_url": final_url
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }), 500


@app.route("/debug", methods=["GET"])
def debug():
    """Route de test pour verifier la connexion sans faire de reservation"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = browser.new_page()
            page.goto("https://zonereservee.coteetsport.ma/login", timeout=30000, wait_until="domcontentloaded")
            time.sleep(2)
            html = page.content()[:2000]
            screenshot = page.screenshot()
            b64 = base64.b64encode(screenshot).decode("utf-8")
            browser.close()
        return jsonify({
            "status": "ok",
            "html_preview": html,
            "screenshot": f"data:image/png;base64,{b64}",
            "email_configured": bool(MDJS_EMAIL),
            "password_configured": bool(MDJS_PASSWORD)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
