from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os

app = Flask(__name__)

# Configuration optimisée du CORS :
# On autorise toutes les origines (*) et on s'assure que les méthodes 
# et les en-têtes (headers) comme 'Content-Type' passent sans blocage.
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Bot actif et prêt !"})

@app.route("/", methods=["POST", "OPTIONS"]) # Ajout de OPTIONS pour le "pre-flight" CORS
def generer_barcode():
    """
    Reçoit : {"match": "Equipe A vs Equipe B", "prono": "1"}
    Renvoie : {"status": "success", "barcode_url": "https://..."}
    """
    # Gestion des requêtes de vérification du navigateur (Pre-flight)
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(force=True, silent=True)

    if not data or "match" not in data or "prono" not in data:
        return jsonify({
            "status": "error", 
            "error": "Champs 'match' et 'prono' requis"
        }), 400

    match = data["match"]
    prono = data["prono"]

    print(f"[BOT] Match reçu : {match} | Prono : {prono}")

    # --- Exemple : génération d'un code-barres fictif ---
    # Cette URL génère une image réelle de code-barres basée sur tes données
    barcode_url = f"https://barcodeapi.org/api/128/{match.replace(' ', '_')}_{prono}"

    return jsonify({
        "status": "success",
        "barcode_url": barcode_url
    })

if __name__ == "__main__":
    # Railway utilise la variable d'environnement PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
