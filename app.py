from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route("/", methods=["GET", "POST", "OPTIONS"])
def unique_endpoint():
    # 1. Gestion du test navigateur (GET)
    if request.method == "GET":
        return jsonify({"status": "ok", "message": "Bot actif et prêt !"})

    # 2. Gestion de la sécurité (OPTIONS)
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # 3. Gestion de Lovable (POST)
    data = request.get_json(force=True, silent=True)
    
    if not data or "match" not in data or "prono" not in data:
        return jsonify({"status": "error", "message": "Données match/prono manquantes"}), 400

    match = data["match"]
    prono = data["prono"]
    match_clean = match.replace(" ", "_").replace("/", "-")
    barcode_url = f"https://barcodeapi.org{match_clean}_{prono}"

    return jsonify({
        "status": "success",
        "barcode_url": barcode_url
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
