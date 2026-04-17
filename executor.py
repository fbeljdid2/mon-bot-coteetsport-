# PariMatchia Bot - executor.py
# Automatise le passage du ticket sur coteetsport.ma avec Playwright
# Sélecteurs CSS inspectés directement sur le site (moteur nSoft/Sisal MDJS)

# ─────────────────────────────────────────────────────────────────────────────
# ANATOMIE DU DOM coteetsport.ma — inspectée en avril 2025
# ─────────────────────────────────────────────────────────────────────────────
#
# 1. BOUTONS DE COTE (1 / X / 2)
#    <button class="btn btn-quota js-bet-btn"
#            data-id="<eventId>_<marketId>_<outcomeId>"
#            data-bet-type="1|X|2"
#            data-quota="1.43"
#            data-event-id="<eventId>">
#
#    → Sélecteur pour cliquer : button[data-id="<sel_id>"]
#
# 2. PANNEAU TICKET / COUPON (à droite)
#    <div class="js-ticket ticket-container">
#      ...sélections ajoutées...
#      <input class="js-stake-input" type="number" placeholder="Mise">
#      <button class="js-print-btn btn btn-primary">Réserver</button>
#    </div>
#
# 3. CHAMP DE MISE
#    input.js-stake-input   (ou  input[name="stake"])
#
# 4. BOUTON RÉSERVER (génère le code-barres)
#    button.js-print-btn    (texte : "Réserver" ou "Générer le billet")
#
# 5. CODE-BARRES généré (après clic Réserver)
#    La page affiche une modale ou redirige vers une page de confirmation :
#    img.barcode-img        (ou  canvas#barcode  ou  .ticket-barcode img)
#    Si le site ouvre une nouvelle fenêtre/onglet, on switche dessus.
#
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import base64
import os
import httpx
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from twocaptcha import TwoCaptcha

SITE_URL      = "https://www.coteetsport.ma"
FOOTBALL_URL  = f"{SITE_URL}/cote-sport/sport/football"
TWOCAPTCHA_KEY = os.environ.get("TWOCAPTCHA_API_KEY", "")
BASE44_API_URL = os.environ.get("BASE44_WEBHOOK_URL", "")

solver = TwoCaptcha(TWOCAPTCHA_KEY) if TWOCAPTCHA_KEY else None


async def solve_recaptcha_if_present(page):
    """Détecte et résout un reCAPTCHA sur la page courante via 2captcha."""
    try:
        captcha_el = await page.query_selector(".g-recaptcha[data-sitekey]")
        if not captcha_el or not solver:
            return
        site_key = await captcha_el.get_attribute("data-sitekey")
        if not site_key:
            return
        print("🔐 reCAPTCHA détecté — résolution 2captcha...")
        result = solver.recaptcha(sitekey=site_key, url=page.url)
        token  = result.get("code", "")
        await page.evaluate(
            f"document.getElementById('g-recaptcha-response').innerHTML = '{token}';"
        )
        await asyncio.sleep(1)
        print("✅ reCAPTCHA résolu")
    except Exception as e:
        print(f"[captcha] Pas de reCAPTCHA ou erreur ignorée: {e}")


async def execute_ticket(payload: dict):
    """
    Passe un ticket complet sur coteetsport.ma :
      1. Charge la page football
      2. Clique sur chaque bouton de cote via  button[data-id='<sel_id>']
      3. Saisit la mise dans  input.js-stake-input
      4. Clique sur  button.js-print-btn  (Réserver)
      5. Capture l'image du code-barres et l'envoie à l'application
    """
    ticket_id    = payload.get("ticket_id")
    selection_ids = payload.get("ids", [])
    mise         = payload.get("mise", 0)
    ticket_code  = payload.get("ticket_code")

    print(f"🎯 Ticket {ticket_code} — {len(selection_ids)} sélections — {mise} MAD")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                  "--window-size=1920,1080"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            locale="fr-FR",
            viewport={"width": 1920, "height": 1080}
        )
        # Masquer Playwright (éviter la détection bot)
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        page = await context.new_page()
        barcode_b64 = None

        try:
            # ── 1. Charger la page football ───────────────────────────────
            await page.goto(FOOTBALL_URL, wait_until="networkidle", timeout=40000)
            await solve_recaptcha_if_present(page)

            # Attendre que les boutons de cotes soient présents
            await page.wait_for_selector("button.btn-quota, button.js-bet-btn", timeout=20000)
            print("✅ Page chargée")

            # ── 2. Cliquer sur chaque sélection ───────────────────────────
            for sel_id in selection_ids:
                # Sélecteur exact : button portant data-id="<sel_id>"
                selector = f"button[data-id='{sel_id}']"
                try:
                    btn = await page.wait_for_selector(selector, timeout=8000)
                    await btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.4)
                    await btn.click()
                    print(f"✅ Clic cote  data-id={sel_id}")
                    await asyncio.sleep(0.6)
                except PlaywrightTimeout:
                    # Le match n'est peut-être pas visible : chercher dans la liste complète
                    print(f"⚠️  Sélection {sel_id} non trouvée sur cette page, on continue")

            # ── 3. Saisir la mise ─────────────────────────────────────────
            # input.js-stake-input  (panneau ticket à droite)
            stake_selector = "input.js-stake-input, input[name='stake'], .js-ticket input[type='number']"
            try:
                stake_input = await page.wait_for_selector(stake_selector, timeout=8000)
                await stake_input.click(triple_click=True)  # sélectionner tout
                await stake_input.type(str(mise), delay=80)
                print(f"💰 Mise {mise} MAD saisie")
                await asyncio.sleep(0.5)
            except PlaywrightTimeout:
                print("❌ Champ mise introuvable")

            # ── 4. Cliquer sur Réserver ───────────────────────────────────
            # button.js-print-btn  (libellé : "Réserver" / "Générer le billet")
            reserve_selector = "button.js-print-btn, button.js-generate-barcode, .js-ticket button.btn-primary"
            try:
                reserve_btn = await page.wait_for_selector(reserve_selector, timeout=8000)
                await reserve_btn.click()
                print("📊 Clic Réserver")
                await asyncio.sleep(4)  # attendre la génération du code-barres
            except PlaywrightTimeout:
                print("❌ Bouton Réserver introuvable")

            # ── 5. Capturer le code-barres ────────────────────────────────
            # Après le clic, le site affiche l'image dans :
            #   img.barcode-img  ou  canvas#barcode  ou  .ticket-barcode img
            barcode_selectors = [
                "img.barcode-img",
                "canvas#barcode",
                ".ticket-barcode img",
                ".barcode-container img",
                "img[alt*='arcode']",
                ".js-barcode-img",
            ]
            for sel in barcode_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=6000)
                    barcode_b64 = await el.screenshot(type="png")
                    barcode_b64 = base64.b64encode(barcode_b64).decode()
                    print(f"📸 Code-barres capturé via {sel}")
                    break
                except PlaywrightTimeout:
                    continue

            if not barcode_b64:
                # Fallback : screenshot du panneau ticket complet
                try:
                    ticket_panel = await page.query_selector(".js-ticket, .ticket-container, #ticket-panel")
                    if ticket_panel:
                        shot = await ticket_panel.screenshot(type="png")
                        barcode_b64 = base64.b64encode(shot).decode()
                        print("📸 Screenshot panneau ticket (fallback)")
                    else:
                        shot = await page.screenshot(type="png", full_page=False)
                        barcode_b64 = base64.b64encode(shot).decode()
                        print("📸 Screenshot page complète (dernier recours)")
                except Exception as e:
                    print(f"❌ Screenshot impossible: {e}")

            # ── 6. Envoyer l'image à l'application ────────────────────────
            if barcode_b64 and ticket_id and BASE44_API_URL:
                image_url = f"data:image/png;base64,{barcode_b64}"
                async with httpx.AsyncClient() as client:
                    await client.post(BASE44_API_URL, json={
                        "ticket_id": ticket_id,
                        "barcode_image": image_url,
                        "status": "validated"
                    }, timeout=15)
                print(f"✅ Image envoyée pour ticket {ticket_id}")

        except Exception as e:
            print(f"❌ Erreur générale executor: {e}")
            if ticket_id and BASE44_API_URL:
                async with httpx.AsyncClient() as client:
                    await client.post(BASE44_API_URL, json={
                        "ticket_id": ticket_id,
                        "status": "failed",
                        "error": str(e)
                    }, timeout=10)
        finally:
            await browser.close()
