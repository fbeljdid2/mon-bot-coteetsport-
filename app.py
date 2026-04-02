from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)

# Autorise Lovable à envoyer des requêtes à ton bot
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route("/", methods=["GET"])
def health():
    """Vérifie si le bot est en ligne"""
    return jsonify({"status": "ok", "message": "Bot Sisal/MDJS actif !"})

@app.route("/", methods=["POST", "OPTIONS"])
def generer_barcode():
    """
    Reçoit les données de Lovable et génère le code-barres.
    Format attendu : {"match": "Nom", "prono": "1"}
    """
    # Gestion de la vérification de sécurité du navigateur
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # Récupération des données envoyées par Lovable
    data = request.get_json(force=True, silent=True)

    if not data or "match" not in data or "prono" not in data:
        return jsonify({
            "status": "error", 
            "error": "Données manquantes (match ou prono)"
        }), 400

    match = data["match"]
    prono = data["prono"]

    print(f"[BOT] Requête reçue pour : {match} | Pronostic : {prono}")

    # Génération de l'URL du code-barres (Format Code 128)
    # On nettoie le nom du match pour l'URL
    match_clean = match.replace(" ", "_").replace("/", "-")
    barcode_url = f"https://barcodeapi.org{match_clean}_{prono}"

    # Réponse que Lovable va lire pour afficher l'image
    return jsonify({
        "status": "success",
        "barcode_url": barcode_url
    })

if __name__ == "__main__":
    # Railway définit automatiquement le port via cette variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
