import requests
import json
import os

SERVER_URL = "http://127.0.0.1:8000/scores"
LOCAL_FILE = "scores.json"

def send_score_to_server(username, score):
    data = {"username": username, "score": score}
    try:
    
        response = requests.post(SERVER_URL, json=data, timeout=3)
        if response.status_code == 200:
            print("Rezultāts veiksmīgi nosūtīts uz serveri!")
            return True
    except requests.exceptions.RequestException:
        print("Serveris nav pieejams. Saglabājam lokāli...")
        save_local_score(username, score)
    return False

def save_local_score(username, score):

    scores = []
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, "r") as f:
                scores = json.load(f)
        except:
            scores = []
            
    scores.append({"username": username, "score": score})
    
    with open(LOCAL_FILE, "w") as f:
        json.dump(scores, f, indent=4)

