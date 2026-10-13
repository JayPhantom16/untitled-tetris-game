from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import hashlib
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tetris_secret_key_123'
DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Lietotāju tabula
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Rezultātu tabula
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            level INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# HTML lapa ar līderu tabulu un iespēju palaist/uzzināt par spēli
@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Izmantojam MAX(score), lai katrs spēlētājs parādītos tikai 1 reizi ar savu augstāko rezultātu
    cursor.execute('''
        SELECT username, MAX(score) as score, MAX(level) as level 
        FROM scores 
        GROUP BY username 
        ORDER BY score DESC 
        LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    top_players = [{"username": r[0], "score": r[1], "level": r[2]} for r in rows]
    return render_template('index.html', top_players=top_players)

# API: Reģistrācija
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password', '123')
    
    if not username:
        return jsonify({"error": "Nepieciešams lietotājvārds"}), 400
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        # Ja lietotājs jau eksistē, viss kārtībā, ignorējam kļūdu
        pass
    finally:
        conn.close()
        
    return jsonify({"message": "OK"})

# API: Pieteikšanās (Login)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password', '123')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        token = jwt.encode({
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"token": token})
        
    return jsonify({"error": "Nederīgi dati"}), 401

# API: Rezultātu saglabāšana
@app.route('/scores', methods=['POST'])
def post_score():
    data = request.json
    username = data.get('username')
    score = data.get('score', 0)
    level = data.get('level', 1)
    
    if not username:
        return jsonify({"error": "Trūkst lietotājvārda"}), 400
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO scores (username, score, level) VALUES (?, ?, ?)", (username, score, level))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Rezultāts saglabāts"})

# API: Datu saņemšana JSON formātā (klientam)
@app.route('/api/scores', methods=['GET'])
def api_scores():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, MAX(score) as score, MAX(level) as level 
        FROM scores 
        GROUP BY username 
        ORDER BY score DESC 
        LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    scores_list = [{"username": r[0], "score": r[1], "level": r[2]} for r in rows]
    return jsonify(scores_list)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)