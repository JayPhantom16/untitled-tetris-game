import sys
import os
import pygame
import webbrowser
import requests
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game.logic import TetrisGame

pygame.init()
screen = pygame.display.set_mode((400, 640))
pygame.display.set_caption("Untitled Tetris Game")
clock = pygame.time.Clock()

BASE_URL = "http://127.0.0.1:8000"
LOCAL_SCORES_FILE = "scores.json"

state = 'menu'
username = ""
token = None
game = TetrisGame()
drop_counter = 0
leaderboard_data = []

def load_local_scores():
    if os.path.exists(LOCAL_SCORES_FILE):
        try:
            with open(LOCAL_SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_local_score(uname, score, level):
    scores = load_local_scores()
    
    # Pārbaudām, vai šis spēlētājs jau ir sarakstā
    existing_player = next((s for s in scores if s["username"] == uname), None)
    
    if existing_player:
        # Ja jaunais rezultāts ir labāks, atjauninām to
        if score > existing_player["score"]:
            existing_player["score"] = score
            existing_player["level"] = level
    else:
        # Ja spēlētāja vēl nav, pievienojam jaunu ierakstu
        scores.append({"username": uname, "score": score, "level": level})
        
    # Sakārtojam dilstošā secībā pēc punktiem, saglabājam tikai labāko rezultātu katram un paturam TOP 10
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)
    
    unique_scores = []
    seen_users = set()
    for s in scores:
        if s["username"] not in seen_users:
            seen_users.add(s["username"])
            unique_scores.append(s)
            
    unique_scores = unique_scores[:10]
    
    try:
        with open(LOCAL_SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(unique_scores, f, ensure_ascii=False, indent=4)
    except:
        pass

def fetch_leaderboard():
    global leaderboard_data
    try:
        res = requests.get(f"{BASE_URL}/api/scores", timeout=1)
        if res.status_code == 200:
            server_scores = res.json()
            if server_scores:
                # Apstrādājam servera datus, lai katrs spēlētājs būtu tikai 1 reizi
                unique_dict = {}
                for entry in server_scores:
                    uname = entry.get("username")
                    score = entry.get("score", 0)
                    if uname not in unique_dict or score > unique_dict[uname]["score"]:
                        unique_dict[uname] = entry
                
                sorted_scores = sorted(unique_dict.values(), key=lambda x: x["score"], reverse=True)
                leaderboard_data = sorted_scores[:10]
                return
    except:
        pass
    
    # Ja serveris nav pieejams, ņemam datus no lokālā faila
    leaderboard_data = load_local_scores()
    if not leaderboard_data:
        leaderboard_data = [{"username": "Nav datu", "score": 0, "level": 1}]

def draw_text(text, x, y, color=(255, 255, 255), size=28):
    font = pygame.font.SysFont(None, size)
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif state == 'menu':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    state = 'input_name'
                elif event.key == pygame.K_2:
                    fetch_leaderboard()
                    state = 'in_game_leaderboard'
                elif event.key == pygame.K_3:
                    running = False
                    
        elif state == 'in_game_leaderboard':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b or event.key == pygame.K_ESCAPE:
                    state = 'menu'
                    
        elif state == 'input_name':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(username) > 0:
                    try:
                        requests.post(f"{BASE_URL}/register", json={"username": username, "password": "123"}, timeout=1)
                        res = requests.post(f"{BASE_URL}/login", json={"username": username, "password": "123"}, timeout=1)
                        if res.status_code == 200:
                            token = res.json().get("token")
                    except:
                        pass
                    state = 'game'
                    game = TetrisGame()
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    if len(username) < 15 and event.unicode.isalnum():
                        username += event.unicode
                        
        elif state == 'game':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    state = 'pause'
                elif event.key == pygame.K_LEFT:
                    game.current_piece["x"] -= 1
                    if game.check_collision():
                        game.current_piece["x"] += 1
                elif event.key == pygame.K_RIGHT:
                    game.current_piece["x"] += 1
                    if game.check_collision():
                        game.current_piece["x"] -= 1
                elif event.key == pygame.K_DOWN:
                    game.current_piece["y"] += 1
                    if game.check_collision():
                        game.current_piece["y"] -= 1
                elif event.key == pygame.K_UP:
                    game.rotate_piece()
                    
        elif state == 'pause':
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                state = 'game'
                
        elif state == 'game_over':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    # 1. Spēlēt no jauna
                    state = 'game'
                    game = TetrisGame()
                elif event.key == pygame.K_2:
                    # 2. Paskatīties līderu tabulu
                    fetch_leaderboard()
                    state = 'in_game_leaderboard'
                elif event.key == pygame.K_3:
                    # 3. Atvērt vietni (Browser)
                    webbrowser.open(BASE_URL)
                elif event.key == pygame.K_4:
                    # 4. Atgriezties galvenajā izvēlnē
                    state = 'menu'
                    username = ""
                    game = TetrisGame()

    # Spēles loģika
    if state == 'game':
        game.update_gold_status()
        drop_counter += 1
        speed_threshold = max(5, 30 - (game.level - 1) * 5)
        
        if drop_counter > speed_threshold:
            game.current_piece["y"] += 1
            drop_counter = 0
            
            shape = game.current_piece["shape"]
            py = game.current_piece["y"]
            
            if py + len(shape) > game.height or game.check_collision():
                game.current_piece["y"] -= 1
                game.lock_piece()
                
                if game.game_over:
                    state = 'game_over'
                    if username:
                        save_local_score(username, game.score, game.level)
                        try:
                            headers = {"Authorization": f"Bearer {token}"}
                            requests.post(f"{BASE_URL}/scores", json={"username": username, "score": game.score, "level": game.level}, headers=headers, timeout=1)
                        except:
                            pass

    # Zīmēšana
    screen.fill((30, 30, 30))

    if state == 'menu':
        draw_text("ULTIMATE TETRIS GAME", 50, 150, (255, 255, 255), 26)
        draw_text("1: Sākt spēli", 50, 220, (0, 255, 204), 24)
        draw_text("2: Līderu tabula", 50, 260, (255, 215, 0), 24)
        draw_text("3: Iziet", 50, 300, (200, 100, 100), 24)
        
    elif state == 'in_game_leaderboard':
        draw_text("TOP 10 LĪDERU TABULA", 80, 40, (255, 215, 0), 26)
        draw_text("Vieta   Vārds          Punkti   Līm.", 40, 90, (180, 180, 180), 18)
        
        y_offset = 130
        for idx, entry in enumerate(leaderboard_data[:10]):
            uname = entry.get("username", "Player")
            score = entry.get("score", 0)
            lvl = entry.get("level", 1)
            line = f"{idx+1}.      {uname:<12}   {score:<6}   {lvl}"
            
            # TOP 1 tiek izcelts zelta krāsā
            row_color = (255, 215, 0) if idx == 0 else (255, 255, 255)
            draw_text(line, 40, y_offset, row_color, 18)
            y_offset += 32
            
        draw_text("Nospied [B] vai [ESC], lai atgrieztos", 55, 570, (150, 150, 150), 18)
        
    elif state == 'input_name':
        draw_text("Ievadi savu vārdu:", 50, 180)
        draw_text(f"> {username}_", 50, 230, (0, 255, 204))
        draw_text("Nospied [ENTER], lai sāktu", 50, 300, (150, 150, 150))
        
    elif state in ['game', 'pause', 'game_over']:
        block_size = 25
        board_x = 75
        board_y = 70

        for r_idx, row in enumerate(game.board):
            for c_idx, cell in enumerate(row):
                rect = pygame.Rect(board_x + c_idx * block_size, board_y + r_idx * block_size, block_size - 1, block_size - 1)
                if cell is not None:
                    if cell["is_gold"] == 1:
                        color = (255, 215, 0)
                    else:
                        colors = {
                            1: (0, 204, 255),
                            2: (255, 128, 0),
                            3: (153, 51, 255),
                            4: (51, 204, 51),
                            5: (255, 51, 51)
                        }
                        color = colors.get(cell["color_id"], (0, 204, 255))
                else:
                    color = (45, 45, 45)
                pygame.draw.rect(screen, color, rect)

        if game.current_piece and state != 'game_over':
            shape = game.current_piece["shape"]
            px = game.current_piece["x"]
            py = game.current_piece["y"]
            is_gold = game.current_piece.get("gold", 0)
            c_id = game.current_piece.get("color_id", 1)
            
            if is_gold:
                piece_color = (255, 215, 0)
            else:
                colors = {
                    1: (0, 204, 255),
                    2: (255, 128, 0),
                    3: (153, 51, 255),
                    4: (51, 204, 51),
                    5: (255, 51, 51)
                }
                piece_color = colors.get(c_id, (0, 120, 255))

            for r_idx, row in enumerate(shape):
                for c_idx, val in enumerate(row):
                    if val:
                        if py + r_idx >= 0:
                            rect = pygame.Rect(board_x + (px + c_idx) * block_size, board_y + (py + r_idx) * block_size, block_size - 1, block_size - 1)
                            pygame.draw.rect(screen, piece_color, rect)

        draw_text(f"Spēlētājs: {username}", 20, 10)
        draw_text(f"Punkti: {game.score}", 20, 35)
        draw_text(f"Līmenis (1-5): {game.level}", 20, 60)
        draw_text("Bultiņas: Kustība/Griezt | P: Pauze", 20, 600)

        if state == 'pause':
            overlay = pygame.Surface((400, 640))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            draw_text("PAUZE", 160, 280, (255, 255, 0))
            
        elif state == 'game_over':
            overlay = pygame.Surface((400, 640))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            draw_text("SPĒLE BEIGUSIES", 95, 160, (255, 0, 0))
            draw_text(f"Tavs rezultāts: {game.score}", 105, 200, (255, 255, 255))
            
            draw_text("[1] Spēlēt no jauna", 45, 260, (255, 255, 255), 20)
            draw_text("[2] Paskatīties līderu tabulu", 45, 300, (255, 215, 0), 20)
            draw_text("[3] Atvērt vietni (Browser)", 45, 340, (0, 204, 255), 20)
            draw_text("[4] Atgriezties izvēlnē", 45, 380, (200, 100, 100), 20)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()