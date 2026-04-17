# PariMatchia Bot - executor.py
# Automatise le passage du ticket sur coteetsport.ma avec Playwright
# Met à jour le ticket dans Base44 via l'API officielle (PATCH)

import asyncio
import base64
import os
import httpx
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from twocaptcha import TwoCaptcha

SITE_URL        = "https://www.coteetsport.ma"
FOOTBALL_URL    = f"{SITE_URL}/cote-sport/sport/football"
TWOCAPTCHA_KEY  = os.environ.get("TWOCAPTCHA_API_KEY", "")
BASE44_APP_ID   = os.environ.get("BASE44_APP_ID", "")
BASE44_API_KEY  = os.environ.get("BASE44_API_KEY", "")

# URL de base pour mettre à jour une entité Ticket via l'API Base44
# PATCH https://api.base44.com/api/apps/{APP_ID}/entities/Ticket/{ticket_id}
BASE44_BASE_URL = f"https://api.base44.com/api/apps/{BASE44_APP_ID}/entities/Ticket"

solver = TwoCaptcha(TWOCAPTCHA_KEY) if TWOCAPTCHA_KEY else None


async def update_ticket(ticket_id: str, data: dict):
    """Met à jour un ticket dans Base44 via l'API officielle."""
    if not BASE44_APP_ID or not BASE44_API_KEY:
        print("❌ BASE44_APP_ID ou BASE44_API_KEY manquant dans les variables d'environnement !")
        return
    url = f"{BASE44_BASE_URL}/{ticket_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            url,
            headers={
                "api_key": BASE44_API_KEY,
                "Content-Type": "application/json"
            },
            json=data,
            timeout=15
        )
        if resp.status_code in (200, 201):
            print(f"✅ Ticket {ticket_id} mis à jour dans Base44")
        else:
            print(f"❌ Erreur Base44 API: {resp.status_code} — {resp.text}")


async def solve_recaptcha_if_present(page):
    """Détecte et résout un reCAPTCHA via 2captcha si présent."""
    try:
        captcha_el = await page.query_selector(".g-recaptcha[data-sitekey]")
        if not captcha_el or not solver:
            return
        site_key = await captcha_el.get_attribute("data-sitekey")
        if not site_key:
            return
        print("🔐 reCAPTCHA détecté — résolution 2captcha...")
        result = solver.recaptcha(sitekey=site_key, url=page.url)
        token = result.get("code", "")
        await page.evaluate(
            f"document.getElementById('g-recaptcha-response').innerHTML = '{token}';"
        )
        await asyncio.sleep(1)
        print("✅ reCAPTCHA résolu")
    except Exception as e:
        print(f"[captcha] Ignoré: {e}")


async def execute_ticket(payload: dict):
    """
    Passe un ticket complet sur coteetsport.ma :
      1. Charge la page football
      2. Clique sur chaque bouton de cote via button[data-id='<sel_id>']
      3. Saisit la mise dans input.js-stake-input
      4. Clique sur button.js-print-btn (Réserver)
      5. Capture l'image du code-barres
      6. Met à jour le ticket dans Base44 via PATCH API
    """
    ticket_id     = payload.get("ticket_id")
    selection_ids = payload.get("ids", [])
    mise          = payload.get("mise", 0)
    ticket_code   = payload.get("ticket_code")

    print(f"🎯 Ticket {ticket_code} — {len(selection_ids)} sélections — {mise} MAD")

    # Marquer le ticket comme "submitted" dès le début
    await update_ticket(ticket_id, {"status": "submitted"})

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--window-size=1920,1080"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            locale="fr-FR",
            viewport={"width": 1920, "height": 1080}
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await context.new_page()
        barcode_b64 = None

        try:
            # ── 1. Charger la page football ───────────────────────────────
            await page.goto(FOOTBALL_URL, wait_until="networkidle", timeout=40000)
            await solve_recaptcha_if_present(page)
            await page.wait_for_selector("button.btn-quota, button.js-bet-btn", timeout=20000)
            print("✅ Page chargée")

            # ── 2. Cliquer sur chaque sélection ───────────────────────────
            for sel_id in selection_ids:
                selector = f"button[data-id='{sel_id}']"
                try:
                    btn = await page.wait_for_selector(selector, timeout=8000)
                    await btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.4)
                    await btn.click()
                    print(f"✅ Clic cote data-id={sel_id}")
                    await asyncio.sleep(0.7)
                except PlaywrightTimeout:
                    print(f"⚠️  Sélection {sel_id} introuvable, on passe")

            # ── 3. Saisir la mise ─────────────────────────────────────────
            stake_selector = "input.js-stake-input, input[name='stake'], .js-ticket input[type='number']"
            try:
                stake_input = await page.wait_for_selector(stake_selector, timeout=8000)
                await stake_input.click(triple_click=True)
                await stake_input.type(str(int(mise)), delay=80)
                print(f"💰 Mise {mise} MAD saisie")
                await asyncio.sleep(0.5)
            except PlaywrightTimeout:
                print("❌ Champ mise introuvable")

            # ── 4. Cliquer sur Réserver ───────────────────────────────────
            reserve_selector = "button.js-print-btn, button.js-generate-barcode, .js-ticket button.btn-primary"
            try:
                reserve_btn = await page.wait_for_selector(reserve_selector, timeout=8000)
                await reserve_btn.click()
                print("📊 Clic Réserver")
                await asyncio.sleep(5)  # attendre la génération du code-barres
            except PlaywrightTimeout:
                print("❌ Bouton Réserver introuvable")

            # ── 5. Capturer le code-barres ────────────────────────────────
            # Essai dans l'ordre du plus précis au plus large
            for sel in [
                "img.barcode-img",
                "canvas#barcode",
                ".ticket-barcode img",
                ".barcode-container img",
                "img[alt*='arcode']",
                ".js-barcode-img",
            ]:
                try:
                    el = await page.wait_for_selector(sel, timeout=5000)
                    shot = await el.screenshot(type="png")
                    barcode_b64 = base64.b64encode(shot).decode()
                    print(f"📸 Code-barres capturé ({sel})")
                    break
                except PlaywrightTimeout:
                    continue

            if not barcode_b64:
                # Fallback : screenshot du panneau ticket
                ticket_panel = await page.query_selector(".js-ticket, .ticket-container, #ticket-panel")
                if ticket_panel:
                    shot = await ticket_panel.screenshot(type="png")
                else:
                    shot = await page.screenshot(type="png", full_page=False)
                barcode_b64 = base64.b64encode(shot).decode()
                print("📸 Screenshot fallback capturé")

            # ── 6. Mettre à jour le ticket dans Base44 ───────────────────
            await update_ticket(ticket_id, {
                "barcode_image": f"data:image/png;base64,{barcode_b64}",
                "status": "validated"
            })

        except Exception as e:
            print(f"❌ Erreur générale executor: {e}")
            await update_ticket(ticket_id, {"status": "failed", "bot_response": str(e)})
        finally:
            await browser.close()
