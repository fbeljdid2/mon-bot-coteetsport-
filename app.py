from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Bot actif et prêt !"})


@app.route("/", methods=["POST"])
def generer_barcode():
    """
    Reçoit : {"match": "Equipe A vs Equipe B", "prono": "1"}
    Renvoie : {"status": "success", "barcode_url": "https://..."}
    """
    data = request.get_json(force=True, silent=True)

    if not data or "match" not in data or "prono" not in data:
        return jsonify({"status": "error", "error": "Champs 'match' et 'prono' requis"}), 400

    match = data["match"]
    prono = data["prono"]

    print(f"[BOT] Match reçu : {match} | Prono : {prono}")

    # ============================================================
    # TODO : Remplace cette section par ta vraie logique
    # Par exemple : automatisation Selenium sur coteetsport.ma,
    # appel à une API tierce, génération d'image, etc.
    # ============================================================

    # --- Exemple : génération d'un code-barres fictif ---
    # En production, tu remplacerais par l'URL réelle du barcode
    barcode_url = f"https://barcodeapi.org/api/128/{match.replace(' ', '_')}_{prono}_{int(time.time())}"

    return jsonify({
        "status": "success",
        "barcode_url": barcode_url
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
