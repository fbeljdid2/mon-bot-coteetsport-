from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Modèle de données pour recevoir tes pronostics
class Pronostic(BaseModel):
    match_id: str
    pronostic: str # ex: "1", "X", ou "2"

@app.get("/")
def home():
    return {"status": "Le bot est en ligne"}

@app.post("/generer-codebarre")
async def generer_code(pronos: List[Pronostic]):
    # C'est ici qu'on placera le code qui :
    # 1. Ouvre le navigateur
    # 2. Va sur coteetsport.ma
    # 3. Remplit le panier
    # 4. Récupère l'image du code-barres
    
    print(f"Reçu : {pronos}")
    
    return {
        "message": "Tentative de génération du code-barres",
        "url_code_barre": "Lien_vers_l_image_generee"
    }
