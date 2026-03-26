from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot en ligne !"

@app.route('/test-clic')
def test_clic():
    return "Test réussi - prêt pour Selenium."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
