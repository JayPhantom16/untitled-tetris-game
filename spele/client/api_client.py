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