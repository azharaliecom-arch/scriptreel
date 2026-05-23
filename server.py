from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    return jsonify({"success": True})

@app.route("/download")
def download():
    return jsonify({"message": "coming soon"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
