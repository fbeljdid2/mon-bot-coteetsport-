from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route("/", methods=["GET", "POST", "OPTIONS"])
def unique_endpoint():
    if request.method == "GET":
        return jsonify({"status": "ok", "message": "Bot Sisal/MDJS prêt !"})

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(force=True, silent=True)
    
    if not data or "match" not in data or "prono" not in data:
        return jsonify({"status": "error", "message": "Données manquantes"}), 400

    # Nettoyage des données pour un code-barres propre
    match = str(data["match"]).replace(" ", "_").replace("/", "-")
    prono = str(data["prono"])
    
    # URL spécifique pour le format Code 128
    barcode_url = f"https://barcodeapi.org/api/128/{match}_{prono}"

    return jsonify({
        "status": "success",
        "barcode_url": barcode_url
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
