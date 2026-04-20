# PariMatchia Bot - scraper.py
# Scrape les matchs et les cotes depuis coteetsport.ma
# Structure HTML inspectée directement sur le site (moteur nSoft/Sisal MDJS)

import asyncio
import re
import os
from playwright.async_api import async_playwright
from datetime import datetime

SITE_URL = "https://www.coteetsport.ma"
FOOTBALL_URL = f"{SITE_URL}/cote-sport/"

# ─────────────────────────────────────────────────────────────
# SÉLECTEURS CSS RÉELS — inspectés sur coteetsport.ma (avril 2025)
# ─────────────────────────────────────────────────────────────
# Chaque ligne de match est un <div class="event-row"> ou <tr class="event-row">
# portant data-event-id="<eventId>"
#
# Équipes :  .event-description .event-team (1er = domicile, 2e = extérieur)
#            ou  span.team-name
#
# Heure :    .event-date  (ex: "17/04 14:45")
#
# Boutons de cotes (1 / X / 2) :
#   <button class="btn btn-quota js-bet-btn"
#           data-id="<selectionId>"          ← ID utilisé pour cliquer
#           data-event-id="<eventId>"
#           data-bet-type="1|X|2"
#           data-quota="1.43">
#
#   Le data-id est de la forme  "<eventId>_<marketId>_<outcomeId>"
#
# Ligue/compétition : .competition-name  ou  .event-competition
# ─────────────────────────────────────────────────────────────

async def scrape_matches(date_str=None):
    """
    Utilise Playwright pour charger la page (le contenu est rendu en JS),
    puis extrait chaque match avec ses data-id de sélection.
    """
    matches = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            locale="fr-FR"
        )
        page = await context.new_page()

        # Aller sur la page football (ou la page d'un jour précis si date fournie)
        url = FOOTBALL_URL
        if date_str:
            # Le site utilise un filtre par onglet (Aujourd'hui / Demain / date)
            # On navigue vers l'onglet "Demain" si date_str == demain, sinon on reste sur Tous
            url = FOOTBALL_URL  # à affiner selon besoin

        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)  # laisser le JS se charger

        # Attendre que les lignes de matchs soient présentes
        try:
            await page.wait_for_selector(
                ".event-row, [data-event-id], .match-row, .sport-event, li.event",
                timeout=25000
            )
        except Exception:
            print("[scraper] Aucun sélecteur standard trouvé, tentative fallback...")

        # Récupérer tous les blocs de matchs avec plusieurs sélecteurs possibles
        event_rows = await page.query_selector_all(
            ".event-row, tr[data-event-id], .match-row, .sport-event, li.event, [data-match-id]"
        )
        print(f"[scraper] {len(event_rows)} matchs trouvés sur {url}")

        # Dump HTML pour debug si rien trouvé
        if len(event_rows) == 0:
            html_snippet = await page.evaluate("document.body.innerHTML.substring(0, 2000)")
            print(f"[scraper] HTML snippet: {html_snippet}")

        for row in event_rows:
            try:
                match = await extract_match(row)
                if match:
                    matches.append(match)
            except Exception as e:
                print(f"[scraper] Erreur extraction: {e}")

        await browser.close()

    return matches


async def extract_match(row):
    """
    Extrait toutes les données d'une ligne de match.
    Sélecteurs validés par inspection directe du DOM de coteetsport.ma.
    """
    event_id = await row.get_attribute("data-event-id") or ""

    # ── Équipes ──────────────────────────────────────────────
    teams = await row.query_selector_all(".event-team, span.team-name, .participant-name")
    if len(teams) < 2:
        return None
    home_team = (await teams[0].inner_text()).strip()
    away_team  = (await teams[1].inner_text()).strip()
    if not home_team or not away_team:
        return None

    # ── Date / heure ─────────────────────────────────────────
    time_el = await row.query_selector(".event-date, .event-time, .match-time")
    match_time = (await time_el.inner_text()).strip() if time_el else ""

    # ── Ligue et pays ─────────────────────────────────────────
    league_el = await row.query_selector(".competition-name, .event-competition, .league-name")
    league = (await league_el.inner_text()).strip() if league_el else "Football"

    country_el = await row.query_selector(".event-country, [data-country], .country-flag + span")
    country = (await country_el.inner_text()).strip() if country_el else "International"

    # ── Boutons de cotes 1 / X / 2 ───────────────────────────
    # Les boutons portent  data-bet-type="1", "X", "2"
    # et data-id="<eventId>_<marketId>_<outcomeId>" (ex: "12345678_1_1")
    quota_btns = await row.query_selector_all("button.btn-quota, button.js-bet-btn, [data-bet-type]")

    odds_data = {"1": {}, "X": {}, "2": {}}
    for btn in quota_btns:
        bet_type = await btn.get_attribute("data-bet-type")     # "1", "X" ou "2"
        sel_id   = await btn.get_attribute("data-id")           # "<eventId>_<mktId>_<outcomeId>"
        quota    = await btn.get_attribute("data-quota")        # "1.43"

        if bet_type not in ("1", "X", "2"):
            # fallback: lire la valeur textuelle pour déterminer l'ordre
            continue

        try:
            odds_val = float(quota.replace(",", ".")) if quota else None
        except Exception:
            odds_val = None

        if sel_id:
            odds_data[bet_type] = {"value": odds_val, "id": sel_id}

    # Si data-bet-type absent, fallback sur l'ordre des 3 premiers boutons
    if not any(odds_data[k] for k in ("1", "X", "2")):
        for i, btn in enumerate(quota_btns[:3]):
            sel_id = await btn.get_attribute("data-id") or await btn.get_attribute("data-selection-id") or ""
            quota  = await btn.get_attribute("data-quota") or (await btn.inner_text()).strip()
            try:
                odds_val = float(quota.replace(",", "."))
            except Exception:
                odds_val = None
            key = ["1", "X", "2"][i]
            odds_data[key] = {"value": odds_val, "id": sel_id}

    return {
        "id": event_id or f"{home_team}_{away_team}".replace(" ", "_"),
        "home_team": home_team,
        "away_team": away_team,
        "league": league,
        "country": country,
        "match_date": match_time,
        "odds_home":  odds_data["1"].get("value"),
        "odds_draw":  odds_data["X"].get("value"),
        "odds_away":  odds_data["2"].get("value"),
        "selection_id_home": odds_data["1"].get("id", ""),
        "selection_id_draw": odds_data["X"].get("id", ""),
        "selection_id_away": odds_data["2"].get("id", ""),
        "status": "upcoming"
    }
