from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)

# Configuration CORS "Ultra-Permissive" pour Lovable
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@app.route("/", methods=["GET", "POST", "OPTIONS"])
def unique_endpoint():
    # 1. Gestion du test navigateur ou de la vérification Lovable (GET)
    if request.method == "GET":
        return jsonify({
            "status": "ok", 
            "message": "Bot Sisal/MDJS actif et prêt !",
            "usage": "Envoyez un POST avec {'match': '...', 'prono': '...'}"
        })

    # 2. Gestion de la sécurité du navigateur (OPTIONS)
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # 3. Gestion de la création du code-barres (POST)
    try:
        # Récupération des données envoyées par Lovable
        data = request.get_json(force=True, silent=True)
        
        if not data or "match" not in data or "prono" not in data:
            return jsonify({
                "status": "error", 
                "message": "Données 'match' ou 'prono' manquantes dans le JSON"
            }), 400

        match = data["match"]
        prono = data["prono"]
        
        # Nettoyage simple pour l'URL du code-barres
        match_clean = str(match).replace(" ", "_").replace("/", "-")
        
        # Génération de l'URL de l'image (Format Code 128)
        barcode_url = f"https://barcodeapi.org{match_clean}_{prono}"

        # Réponse renvoyée à Lovable
        return jsonify({
            "status": "success",
            "barcode_url": barcode_url,
            "received": {"match": match, "prono": prono}
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Utilisation du port fourni par Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
