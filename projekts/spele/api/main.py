from flask import Flask, render_template, request, jsonify
import sqlite3
import hashlib
import jwt
import datetime
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tetris_secret_key_123'
DB_PATH = "database.db"
LOCAL_SCORES_FILE = "scores.json"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
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

def sync_json_to_db():
    """Automātiski iebaro datus no scores.json uz SQLite datubāzi, ja tādi tur eksistē"""
    if os.path.exists(LOCAL_SCORES_FILE):
        try:
            with open(LOCAL_SCORES_FILE, "r", encoding="utf-8") as f:
                local_scores = json.load(f)
                
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            for entry in local_scores:
                uname = entry.get("username")
                score = entry.get("score", 0)
                level = entry.get("level", 1)
                
                # Pārbaudām vai šāds rezultāts jau eksistē, lai nepārtraukti nedublētu
                cursor.execute(
                    "SELECT id FROM scores WHERE username = ? AND score = ?", 
                    (uname, score)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO scores (username, score, level) VALUES (?, ?, ?)", 
                        (uname, score, level)
                    )
            conn.commit()
            conn.close()
        except:
            pass

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    sync_json_to_db() # Sinhronizē datus pirms parādīšanas
    
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
    
    top_players = [{"username": r[0], "score": r[1], "level": r[2]} for r in rows]
    return render_template('index.html', top_players=top_players)

@app.route('/rules')
def rules():
    return render_template('rules.html')

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
        pass
    finally:
        conn.close()
        
    return jsonify({"message": "OK"})

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

@app.route('/api/scores', methods=['GET'])
def api_scores():
    sync_json_to_db() # Sinhronizē datus arī priekš klienta API
    
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