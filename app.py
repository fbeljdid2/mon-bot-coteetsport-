from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot coteetsport OK"

@app.route("/test-clic")
def test_clic():
    return "Route test-clic OK"
