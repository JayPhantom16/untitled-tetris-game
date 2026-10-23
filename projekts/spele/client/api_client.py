<<<<<<< HEAD
import requests

BASE_URL = "http://127.0.0.1:8000"
auth_token = None

def login_user(username, password):
    global auth_token
    try:
        response = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password}, timeout=3)
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token") # Saglabājam tokenu
            return auth_token
    except requests.exceptions.RequestException:
        print("Serveris nav pieejams!")
    return None

def send_score(score, level):
    if not auth_token:
        print("Nav autorizācijas, nevar nosūtīt punktus!")
        return
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"} # Pievienojam tokenu pieprasījumam
        payload = {"score": score, "level": level}
        response = requests.post(f"{BASE_URL}/scores", json=payload, headers=headers, timeout=3)
        if response.status_code == 201:
            print("Punkti saglabāti serverī!")
    except requests.exceptions.RequestException:
        pass
=======
import requests
import json
import os

SERVER_URL = "http://127.0.0.1:8000/scores"
LOCAL_FILE = "scores.json"

def send_score_to_server(username, score):
    data = {"username": username, "score": score}
    try:
        # Пытаемся отправить данные на сервер через POST
        response = requests.post(SERVER_URL, json=data, timeout=3)
        if response.status_code == 200:
            print("Rezultāts veiksmīgi nosūtīts uz serveri!")
            return True
    except requests.exceptions.RequestException:
        print("Serveris nav pieejams. Saglabājam lokāli...")
        save_local_score(username, score)
    return False

def save_local_score(username, score):
    # Сохранение в кеш-файл scores.json при отсутствии сети
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
>>>>>>> b8fdab76fa7ba2f49bb8fb796cf5ebd7d484c39e
