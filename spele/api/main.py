from flask import Flask, render_template, request, jsonify
import os
import json

app = Flask(__name__)
SCORES_FILE = "scores.json"

def get_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

@app.route("/")
def index():
    scores = get_scores()
    # Sakārtojam un paņemam TOP 10
    top_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    return render_template("index.html", scores=top_scores)

@app.route("/rules")
def rules():
    return render_template("rules.html")

@app.route("/api/scores", methods=["GET"])
def api_scores():
    return jsonify(get_scores())

@app.route("/scores", methods=["POST"])
def post_score():
    data = request.json
    if not data or "username" not in data or "score" not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    scores = get_scores()
    scores.append({
        "username": data["username"],
        "score": data["score"],
        "level": data.get("level", 1)
    })
    
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=4)
        
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)