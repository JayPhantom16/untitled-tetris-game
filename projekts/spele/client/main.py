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

# ---------------------------------------------------------------------------
# dizains
# ---------------------------------------------------------------------------
BG_TOP = (18, 20, 34)
BG_BOTTOM = (34, 28, 56)
GRID_COLOR = (38, 40, 58)
ACCENT = (0, 255, 204)
GOLD = (255, 215, 0)
SILVER = (200, 200, 210)
BRONZE = (205, 127, 50)
MUTED = (205, 205, 225)
PANEL_BORDER = (120, 120, 160)

COLORS = {
    1: (0, 204, 255),
    2: (255, 128, 0),
    3: (153, 51, 255),
    4: (51, 204, 51),
    5: (255, 51, 51),
}

_fonts = {}
_text_cache = {}


def get_font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont("segoeui,arial,helvetica", size, bold=True)
    return _fonts[size]


def render_text(text, color, size):
    key = (text, color, size)
    img = _text_cache.get(key)
    if img is None:
        if len(_text_cache) > 400:
            _text_cache.clear()
        font = get_font(max(12, int(size * 0.92)))
        base = font.render(text, True, color)
        outline = font.render(text, True, (0, 0, 0))
        w, h = base.get_size()
        img = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx or dy:
                    img.blit(outline, (3 + dx, 3 + dy))
        img.blit(base, (3, 3))
        _text_cache[key] = img
    return img


def draw_text(text, x, y, color=(255, 255, 255), size=28, center=False, shadow=True):
    img = render_text(text, color, size)
    if center:
        x = (screen.get_width() - (img.get_width() - 6)) // 2
    screen.blit(img, (x - 3, y - 3))


def shade(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in color)


def draw_block(x, y, size, color):
    pygame.draw.rect(screen, color, (x, y, size - 1, size - 1), border_radius=4)
    light = shade(color, 1.35)
    dark = shade(color, 0.6)
    pygame.draw.line(screen, light, (x + 2, y + 1), (x + size - 4, y + 1), 2)
    pygame.draw.line(screen, light, (x + 1, y + 2), (x + 1, y + size - 4), 2)
    pygame.draw.line(screen, dark, (x + 2, y + size - 3), (x + size - 3, y + size - 3), 2)
    pygame.draw.line(screen, dark, (x + size - 3, y + 2), (x + size - 3, y + size - 3), 2)
    pygame.draw.rect(screen, shade(color, 1.15), (x + 5, y + 5, size - 11, size - 11), border_radius=2)


def draw_gold_block(x, y, size):
    draw_block(x, y, size, GOLD)
    pygame.draw.circle(screen, (255, 250, 200), (x + size // 2, y + size // 2), 3)


def draw_panel(rect, alpha=60, radius=10, border=None):

    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (8, 8, 20, min(235, 140 + alpha * 4)), s.get_rect(), border_radius=radius)
    screen.blit(s, (rect[0], rect[1]))
    if border:
        pygame.draw.rect(screen, border, rect, 1, border_radius=radius)


def make_background():
    bg = pygame.Surface((400, 640))
    for y in range(640):
        t = y / 640
        c = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3))
        pygame.draw.line(bg, c, (0, y), (400, y))
    return bg


def make_overlay(alpha):
    s = pygame.Surface((400, 640))
    s.set_alpha(alpha)
    s.fill((0, 0, 0))
    return s


background = make_background()
overlay_pause = make_overlay(180)
overlay_over = make_overlay(200)

# ---------------------------------------------------------------------------
# dati
# ---------------------------------------------------------------------------
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
    
    player_found = False
    for entry in scores:
        if entry["username"] == uname:
            player_found = True
            if score > entry["score"]:
                entry["score"] = score
                entry["level"] = level
            break
            
    if not player_found:
        scores.append({"username": uname, "score": score, "level": level})
    
    unique_scores = {}
    for s in scores:
        uname_key = s["username"]
        if uname_key not in unique_scores or s["score"] > unique_scores[uname_key]["score"]:
            unique_scores[uname_key] = s
            
    scores = sorted(list(unique_scores.values()), key=lambda x: x["score"], reverse=True)[:10]
    
    try:
        with open(LOCAL_SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=4)
    except:
        pass

def fetch_leaderboard():
    global leaderboard_data
    try:
        res = requests.get(f"{BASE_URL}/api/scores", timeout=1)
        if res.status_code == 200:
            server_scores = res.json()
            if server_scores:
                leaderboard_data = sorted(server_scores, key=lambda x: x["score"], reverse=True)[:10]
                return
    except:
        pass
    
    leaderboard_data = load_local_scores()
    if not leaderboard_data:
        leaderboard_data = [{"username": "Nav datu", "score": 0, "level": 1}]

# ---------------------------------------------------------------------------
# galv cikls
# ---------------------------------------------------------------------------
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
                    # Atvērt vietni no galvenās izvēlnes
                    webbrowser.open(BASE_URL)
                elif event.key == pygame.K_4:
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
                elif event.key == pygame.K_UP:
                    game.rotate_piece()
                    
        elif state == 'pause':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    state = 'game'  # Atgriezties spēlē
                elif event.key == pygame.K_m or event.key == pygame.K_b:
                    state = 'menu'  # Atgriezties galvenajā izvēlnē
                elif event.key == pygame.K_q:
                    running = False # Iziet no spēles pilnībā
                elif event.key == pygame.K_l:
                    webbrowser.open(BASE_URL) # Atvērt vietni arī pauzes laikā, ja vajag
                
        elif state == 'game_over':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    state = 'game'
                    game = TetrisGame()
                elif event.key == pygame.K_2:
                    fetch_leaderboard()
                    state = 'in_game_leaderboard'
                elif event.key == pygame.K_3:
                    webbrowser.open(BASE_URL)
                elif event.key == pygame.K_b:
                    state = 'menu'

    # Spēles loģika
    if state == 'game':
        game.update_gold_status()
        drop_counter += 1
        speed_threshold = max(5, 30 - (game.level - 1) * 5)
        
        if pygame.key.get_pressed()[pygame.K_DOWN]:
            speed_threshold = min(speed_threshold, 2)
        
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
    screen.blit(background, (0, 0))

    if state == 'menu':
        draw_text("UNTITLED TETRIS GAME", 0, 110, (255, 255, 255), 30, center=True)
        pygame.draw.line(screen, ACCENT, (60, 155), (340, 155), 2)
        draw_panel((40, 180, 320, 190), 20, 14, PANEL_BORDER)
        draw_text("1: Sākt spēli", 70, 200, (0, 255, 204), 22)
        draw_text("2: Līderu tabula", 70, 240, (255, 215, 0), 22)
        draw_text("3: Atvērt vietni (Browser)", 70, 280, (0, 204, 255), 22)
        draw_text("4: Iziet", 70, 320, (255, 130, 130), 22)
        
    elif state == 'in_game_leaderboard':
        draw_text("TOP 10 LĪDERU TABULA", 0, 35, GOLD, 28, center=True)
        pygame.draw.line(screen, GOLD, (60, 75), (340, 75), 2)

        hdr = (230, 230, 240)
        draw_text("Vieta", 40, 90, hdr, 18)
        draw_text("Vārds", 105, 90, hdr, 18)
        draw_text("Punkti", 245, 90, hdr, 18)
        draw_text("Līm.", 325, 90, hdr, 18)
        
        y_offset = 130
        for idx, entry in enumerate(leaderboard_data[:10]):
            uname = entry.get("username", "Player")
            score = entry.get("score", 0)
            lvl = entry.get("level", 1)

            if idx == 0:
                row_color = GOLD
            elif idx == 1:
                row_color = SILVER
            elif idx == 2:
                row_color = BRONZE
            else:
                row_color = (255, 255, 255)

            if idx % 2 == 0:
                draw_panel((30, y_offset - 4, 340, 28), 14, 6)
            draw_text(f"{idx+1}.", 48, y_offset, row_color, 18)
            draw_text(str(uname), 105, y_offset, row_color, 18)
            draw_text(str(score), 245, y_offset, row_color, 18)
            draw_text(str(lvl), 335, y_offset, row_color, 18)
            y_offset += 32
            
        draw_text("Nospied [B] vai [ESC], lai atgrieztos", 0, 570, MUTED, 18, center=True)
        
    elif state == 'input_name':
        draw_text("Ievadi savu vārdu:", 50, 180)
        draw_panel((40, 222, 320, 44), 25, 8, ACCENT)
        cursor = "_" if (pygame.time.get_ticks() // 500) % 2 else " "
        draw_text(f"> {username}{cursor}", 55, 230, (0, 255, 204))
        draw_text("Nospied [ENTER], lai sāktu", 50, 300, MUTED)
        
    elif state in ['game', 'pause', 'game_over']:
        block_size = 25
        board_x = 75
        board_y = 70
        rows = len(game.board)
        cols = len(game.board[0])

        
        frame = pygame.Rect(board_x - 6, board_y - 6, cols * block_size + 12, rows * block_size + 12)
        pygame.draw.rect(screen, (10, 10, 20), frame, border_radius=8)
        pygame.draw.rect(screen, ACCENT, frame, 2, border_radius=8)

        for r_idx, row in enumerate(game.board):
            for c_idx, cell in enumerate(row):
                x = board_x + c_idx * block_size
                y = board_y + r_idx * block_size
                if cell is not None:
                    if cell["is_gold"] == 1:
                        draw_gold_block(x, y, block_size)
                    else:
                        draw_block(x, y, block_size, COLORS.get(cell["color_id"], COLORS[1]))
                else:
                    pygame.draw.rect(screen, GRID_COLOR, (x, y, block_size, block_size), 1)

        if game.current_piece and state != 'game_over':
            shape = game.current_piece["shape"]
            px = game.current_piece["x"]
            py = game.current_piece["y"]
            is_gold = game.current_piece.get("gold", 0)
            c_id = game.current_piece.get("color_id", 1)
            piece_color = COLORS.get(c_id, COLORS[1])

            for r_idx, row in enumerate(shape):
                for c_idx, val in enumerate(row):
                    if val and py + r_idx >= 0:
                        x = board_x + (px + c_idx) * block_size
                        y = board_y + (py + r_idx) * block_size
                        if is_gold:
                            draw_gold_block(x, y, block_size)
                        else:
                            draw_block(x, y, block_size, piece_color)

        # HUD 
        draw_panel((10, 4, 380, 56), 25, 10, PANEL_BORDER)
        draw_text(f"Spēlētājs: {username}", 20, 9, (255, 255, 255), 19)
        draw_text(f"Punkti: {game.score}", 20, 33, ACCENT, 19)
        draw_text(f"Līmenis (1-5): {game.level}", 190, 33, GOLD, 19)
        draw_text("Bultiņas: Kustība/Griezt | P: Pauze", 0, 612, MUTED, 18, center=True)

        if state == 'pause':
            screen.blit(overlay_pause, (0, 0))
            draw_panel((40, 160, 320, 250), 20, 14, PANEL_BORDER)
            
            draw_text("PAUZE", 0, 180, (255, 255, 0), 36, center=True)
            draw_text("[P] Turpināt spēli", 70, 250, (255, 255, 255), 20)
            draw_text("[M] Atgriezties izvēlnē", 70, 290, (255, 215, 0), 20)
            draw_text("[L] Atvērt vietni", 70, 330, (0, 204, 255), 20)
            draw_text("[Q] Iziet no spēles", 70, 370, (255, 100, 100), 20)
            
        elif state == 'game_over':
            screen.blit(overlay_over, (0, 0))
            draw_panel((30, 150, 340, 266), 20, 14, PANEL_BORDER)
            
            draw_text("SPĒLE BEIGUSIES", 0, 168, (255, 0, 0), 30, center=True)
            draw_text(f"Tavs rezultāts: {game.score}", 0, 208, (255, 255, 255), 22, center=True)
            
            draw_text("[1] Spēlēt no jauna", 55, 262, (255, 255, 255), 19)
            draw_text("[2] Paskatīties līderu tabulu", 55, 296, (255, 215, 0), 19)
            draw_text("[3] Atvērt vietni (Browser)", 55, 330, (0, 204, 255), 19)
            draw_text("[B] Atgriezties izvēlnē", 55, 364, (235, 235, 235), 19)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()