# PariMatchia Bot - main.py
# Déployez ce fichier sur Railway avec les autres fichiers du projet

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import uvicorn
from scraper import scrape_matches
from executor import execute_ticket

app = FastAPI(title="PariMatchia Bot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TicketPayload(BaseModel):
    ticket_code: str
    ticket_id: str
    ids: List[str]
    mise: float

@app.get("/")
async def root():
    return {"status": "PariMatchia Bot is running 🚀"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/matches")
async def get_matches(date: Optional[str] = None):
    """Scrape les matchs depuis coteetsport.ma et les retourne"""
    matches = await scrape_matches(date)
    return {"matches": matches, "count": len(matches)}

@app.post("/submit")
async def submit_ticket(payload: TicketPayload, background_tasks: BackgroundTasks):
    """Reçoit un ticket, exécute l'automation et retourne le code-barres"""
    background_tasks.add_task(execute_ticket, payload.dict())
    return {"status": "accepted", "ticket_code": payload.ticket_code}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
