from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Bot is alive!"}), 200

def run():
    """Function to be called from a separate thread."""
    app.run(host='0.0.0.0', port=8080)
