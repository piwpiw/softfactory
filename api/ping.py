from flask import Flask, jsonify, request

app = Flask(__name__)


@app.get("/")
@app.get("/api/ping")
@app.get("/api/ping/")
def ping():
    return jsonify({"ok": True, "runtime": "python", "path": request.path})
