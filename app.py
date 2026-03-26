from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Le bot de Said est enfin EN LIGNE et pret !"

@app.route('/test-clic')
def test():
    return "✅ Le bot arrive a lire cette page !"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
