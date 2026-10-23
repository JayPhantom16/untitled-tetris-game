import sys
import os
import json
import hmac
import hashlib
import webbrowser

import pygame
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game.logic import TetrisGame

pygame.init()
screen = pygame.display.set_mode((400, 640))
pygame.display.set_caption("Untitled Tetris Game")
clock = pygame.time.Clock()

# ---------------------------------------------------------------- Konstantes
# Adresi var nomainīt ar vides mainīgo (piem., uz https://... produkcijā)
BASE_URL = os.environ.get("TETRIS_SERVER", "http://127.0.0.1:8000")
LOCAL_SCORES_FILE = "scores.json"
LOCAL_USERS_FILE = "local_users.json"   # paroļu hash bezsaistes pieteikšanās pārbaudei

FPS = 30

# Mehānika: ja ilgi netiek notīrītas rindas, spēle paātrinās
STRESS_INTERVAL_SEC = 10     # ik pēc cik sekundēm bez rindas notīrīšanas +1 paātrinājuma solis
STRESS_STEP_FRAMES = 2       # par cik kadriem samazinās kritiena slieksnis vienā solī
STRESS_MAX_STEPS = 8         # maksimālais paātrinājuma soļu skaits
MIN_DROP_THRESHOLD = 2       # ātrākais iespējamais kritiens (kadros)

BLOCK_COLORS = {
    1: (0, 204, 255),
    2: (255, 128, 0),
    3: (153, 51, 255),
    4: (51, 204, 51),
    5: (255, 51, 51),
}
GOLD_COLOR = (255, 215, 0)
DEFAULT_COLOR = (0, 204, 255)

# ------------------------------------------------------------------ Stāvoklis
state = 'menu'
auth_action = None      # 'login' vai 'register'
input_step = 'username' # 'username' vai 'password'
username = ""
password = ""
error_msg = ""
token = None
offline_mode = False
game = TetrisGame()
drop_counter = 0
leaderboard_data = []

no_clear_frames = 0     # kadri kopš pēdējās notīrītās rindas
stress_level = 0        # pašreizējais paātrinājuma līmenis

_font_cache = {}


# ------------------------------------------------------------ Lokālie rezultāti
def load_local_scores():
    if os.path.exists(LOCAL_SCORES_FILE):
        try:
            with open(LOCAL_SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
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
        key = s["username"]
        if key not in unique_scores or s["score"] > unique_scores[key]["score"]:
            unique_scores[key] = s

    scores = sorted(unique_scores.values(), key=lambda x: x["score"], reverse=True)[:10]

    try:
        with open(LOCAL_SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


# ------------------------------------------- Lokālie lietotāji (bezsaistes pieteikšanās)
def _hash_password(pwd, salt):
    return hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt, 100_000).hex()


def _load_users():
    if os.path.exists(LOCAL_USERS_FILE):
        try:
            with open(LOCAL_USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def remember_user(uname, pwd):
    """Pēc sekmīgas pieteikšanās serverī saglabā paroles hash bezsaistes režīmam."""
    users = _load_users()
    salt = os.urandom(16)
    users[uname] = {"salt": salt.hex(), "hash": _hash_password(pwd, salt)}
    try:
        with open(LOCAL_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)
    except Exception:
        pass


def verify_local_user(uname, pwd):
    """True / False, ja lietotājs zināms; None, ja lietotājs nav saglabāts lokāli."""
    entry = _load_users().get(uname)
    if not entry:
        return None
    expected = _hash_password(pwd, bytes.fromhex(entry["salt"]))
    return hmac.compare_digest(expected, entry["hash"])


# ------------------------------------------------------------------ Palīgfunkcijas
def fetch_leaderboard():
    global leaderboard_data
    try:
        res = requests.get(f"{BASE_URL}/api/scores", timeout=1)
        if res.status_code == 200:
            server_scores = res.json()
            if server_scores:
                leaderboard_data = sorted(server_scores, key=lambda x: x["score"], reverse=True)[:10]
                return
    except Exception:
        pass

    leaderboard_data = load_local_scores()
    if not leaderboard_data:
        leaderboard_data = [{"username": "Nav datu", "score": 0, "level": 1}]


def get_font(size):
    if size not in _font_cache:
        _font_cache[size] = pygame.font.SysFont(None, size)
    return _font_cache[size]


def draw_text(text, x, y, color=(255, 255, 255), size=28):
    img = get_font(size).render(text, True, color)
    screen.blit(img, (x, y))


def block_color(cell_or_piece_gold, color_id, fallback=DEFAULT_COLOR):
    if cell_or_piece_gold:
        return GOLD_COLOR
    return BLOCK_COLORS.get(color_id, fallback)


def is_logged_in():
    return token is not None or offline_mode


def logout():
    """Izrakstās un atgriežas izvēlnē; nākamā spēle atkal prasīs Login/Register."""
    global token, username, password, state, offline_mode
    token = None
    offline_mode = False
    username = ""
    password = ""
    state = 'menu'


def reset_auth_input(keep_error=False):
    global input_step, username, password, error_msg
    input_step = 'username'
    username = ""
    password = ""
    if not keep_error:
        error_msg = ""


def start_new_game():
    global game, drop_counter, state, no_clear_frames, stress_level
    game = TetrisGame()
    drop_counter = 0
    no_clear_frames = 0
    stress_level = 0
    state = 'game'


def do_auth():
    """Reģistrē (ja vajag) un pārbauda pieteikšanos serverī. Spēle sākas tikai pie veiksmes."""
    global token, error_msg, offline_mode, password
    offline_mode = False
    try:
        if auth_action == 'register':
            res = requests.post(f"{BASE_URL}/register",
                                json={"username": username, "password": password}, timeout=3)
            if res.status_code != 201:
                try:
                    msg = res.json().get("error", "Kļūda reģistrējoties!")
                except Exception:
                    msg = "Kļūda reģistrējoties!"
                reset_auth_input()
                error_msg = msg
                return

        res = requests.post(f"{BASE_URL}/login",
                            json={"username": username, "password": password}, timeout=3)
        if res.status_code == 200 and res.json().get("token"):
            token = res.json()["token"]
            remember_user(username, password)
            error_msg = ""
            start_new_game()
        else:
            reset_auth_input()
            error_msg = "Nederīgs vārds vai parole!"

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        # Serveris nav pieejams -> bezsaistes režīms, bet ar lokālu paroles pārbaudi
        if auth_action == 'register':
            reset_auth_input()
            error_msg = "Reģistrācijai vajadzīgs serveris!"
            return

        result = verify_local_user(username, password)
        if result is True:
            token = None
            offline_mode = True
            error_msg = ""
            start_new_game()
        elif result is False:
            reset_auth_input()
            error_msg = "Nederīgs vārds vai parole!"
        else:
            reset_auth_input()
            error_msg = "Serveris nav pieejams, lietotājs nav saglabāts!"
    except Exception:
        error_msg = "Kļūda pieslēdzoties!"
        input_step = 'username'
        password = ""


def count_board_cells():
    return sum(1 for row in game.board for cell in row if cell is not None)


def lock_and_detect_clear():
    """Fiksē figūru un atgriež True, ja tika notīrīta vismaz viena rinda.
    Atpazīšana: ja pēc fiksēšanas laukumā ir mazāk šūnu, nekā bija + figūras šūnas."""
    piece_cells = sum(1 for row in game.current_piece["shape"] for v in row if v)
    before = count_board_cells()
    game.lock_piece()
    after = count_board_cells()
    return after < before + piece_cells


def get_drop_threshold(is_fast_drop):
    base = max(5, 30 - (game.level - 1) * 5)
    threshold = max(MIN_DROP_THRESHOLD, base - stress_level * STRESS_STEP_FRAMES)
    if is_fast_drop:
        threshold = min(threshold, 2)
    return threshold


# ------------------------------------------------------------------ Galvenais cikls
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif state == 'menu':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    if is_logged_in():
                        start_new_game()
                    else:
                        state = 'auth_choice'
                elif event.key == pygame.K_2:
                    fetch_leaderboard()
                    state = 'in_game_leaderboard'
                elif event.key == pygame.K_3:
                    webbrowser.open(BASE_URL)
                elif event.key == pygame.K_4:
                    running = False
                elif event.key == pygame.K_5 and is_logged_in():
                    logout()

        elif state == 'auth_choice':
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_2):
                    auth_action = 'login' if event.key == pygame.K_1 else 'register'
                    reset_auth_input()
                    state = 'auth_input'
                elif event.key in (pygame.K_b, pygame.K_ESCAPE):
                    state = 'menu'

        elif state == 'auth_input':
            if event.type == pygame.KEYDOWN:
                is_enter = event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)

                if input_step == 'username':
                    if is_enter:
                        if len(username) > 0:
                            input_step = 'password'
                            error_msg = ""
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        state = 'auth_choice'
                    elif len(username) < 15 and event.unicode.isalnum():
                        username += event.unicode

                elif input_step == 'password':
                    if is_enter:
                        if len(password) > 0:
                            do_auth()
                    elif event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        input_step = 'username'
                        password = ""
                    elif len(password) < 20 and event.unicode and event.unicode.isprintable():
                        password += event.unicode

        elif state == 'in_game_leaderboard':
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_b, pygame.K_ESCAPE):
                    state = 'menu'

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
                    state = 'game'
                elif event.key in (pygame.K_m, pygame.K_b):
                    state = 'menu'          # sesija saglabājas
                elif event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_l:
                    webbrowser.open(BASE_URL)

        elif state == 'game_over':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    start_new_game()
                elif event.key == pygame.K_2:
                    fetch_leaderboard()
                    state = 'in_game_leaderboard'
                elif event.key == pygame.K_3:
                    webbrowser.open(BASE_URL)
                elif event.key == pygame.K_b:
                    state = 'menu'          # sesija saglabājas

    # ------------------------------------------------------------ Spēles loģika
    if state == 'game':
        game.update_gold_status()

        # Paātrinājums, ja ilgi nav notīrīta neviena rinda
        no_clear_frames += 1
        stress_level = min(STRESS_MAX_STEPS, no_clear_frames // (STRESS_INTERVAL_SEC * FPS))

        keys = pygame.key.get_pressed()
        speed_threshold = get_drop_threshold(keys[pygame.K_DOWN])

        drop_counter += 1

        if drop_counter > speed_threshold:
            game.current_piece["y"] += 1
            drop_counter = 0

            shape = game.current_piece["shape"]
            py = game.current_piece["y"]

            # (pārbaude par dibenu atstāta, jo nav zināms, vai check_collision to jau dara)
            if py + len(shape) > game.height or game.check_collision():
                game.current_piece["y"] -= 1

                if lock_and_detect_clear():
                    no_clear_frames = 0
                    stress_level = 0

                if game.game_over:
                    state = 'game_over'
                    if username:
                        save_local_score(username, game.score, game.level)
                        if token:
                            try:
                                headers = {"Authorization": f"Bearer {token}"}
                                requests.post(f"{BASE_URL}/scores",
                                              json={"username": username, "score": game.score,
                                                    "level": game.level},
                                              headers=headers, timeout=1)
                            except Exception:
                                pass

    # ---------------------------------------------------------------- Zīmēšana
    screen.fill((30, 30, 30))

    if state == 'menu':
        draw_text("UNTITLED TETRIS GAME", 45, 130, (255, 255, 255), 26)
        start_label = "1: Sākt spēli" if not is_logged_in() else f"1: Sākt spēli ({username})"
        draw_text(start_label, 50, 200, (0, 255, 204), 22)
        draw_text("2: Līderu tabula", 50, 240, (255, 215, 0), 22)
        draw_text("3: Atvērt vietni (Browser)", 50, 280, (0, 204, 255), 22)
        draw_text("4: Iziet", 50, 320, (200, 100, 100), 22)
        if is_logged_in():
            draw_text("5: Iziet no konta", 50, 360, (200, 200, 200), 22)

    elif state == 'auth_choice':
        draw_text("SPĒLES UZSĀKŠANA", 85, 130, (255, 255, 255), 26)
        draw_text("1: Pieteikties (Login)", 50, 210, (0, 255, 204), 22)
        draw_text("2: Reģistrēties (Register)", 50, 260, (255, 215, 0), 22)
        draw_text("[B] Atgriezties", 50, 330, (150, 150, 150), 20)

    elif state == 'auth_input':
        title = "Pieteikšanās" if auth_action == 'login' else "Reģistrācija"
        draw_text(title, 130, 80, (255, 215, 0), 26)

        if error_msg:
            draw_text(error_msg, 40, 130, (255, 80, 80), 18)

        if input_step == 'username':
            draw_text("Ievadiet lietotājvārdu:", 50, 180, (255, 255, 255), 20)
            draw_text(f"> {username}_", 50, 220, (0, 255, 204), 22)
            draw_text("Nospiediet [ENTER]", 50, 280, (150, 150, 150), 16)
        else:
            masked_pass = "*" * len(password)
            draw_text(f"Lietotājs: {username}", 50, 170, (200, 200, 200), 18)
            draw_text("Ievadiet paroli:", 50, 210, (255, 255, 255), 20)
            draw_text(f"> {masked_pass}_", 50, 250, (255, 128, 0), 22)
            draw_text("Nospiediet [ENTER], lai apstiprinātu", 50, 310, (150, 150, 150), 16)

        draw_text("[ESC] Atpakaļ", 50, 400, (150, 150, 150), 16)

    elif state == 'in_game_leaderboard':
        draw_text("TOP 10 LĪDERU TABULA", 80, 40, (255, 215, 0), 26)
        draw_text("Vieta   Vārds          Punkti   Līm.", 40, 90, (180, 180, 180), 18)

        y_offset = 130
        for idx, entry in enumerate(leaderboard_data[:10]):
            uname = entry.get("username", "Player")
            score = entry.get("score", 0)
            lvl = entry.get("level", 1)
            line = f"{idx+1}.      {uname:<12}   {score:<6}   {lvl}"

            row_color = GOLD_COLOR if idx == 0 else (255, 255, 255)
            draw_text(line, 40, y_offset, row_color, 18)
            y_offset += 32

        draw_text("Nospied [B] vai [ESC], lai atgrieztos", 55, 570, (150, 150, 150), 18)

    elif state in ('game', 'pause', 'game_over'):
        block_size = 25
        board_x = 75
        board_y = 70

        for r_idx, row in enumerate(game.board):
            for c_idx, cell in enumerate(row):
                rect = pygame.Rect(board_x + c_idx * block_size, board_y + r_idx * block_size,
                                   block_size - 1, block_size - 1)
                if cell is not None:
                    color = block_color(cell["is_gold"] == 1, cell["color_id"])
                else:
                    color = (45, 45, 45)
                pygame.draw.rect(screen, color, rect)

        if game.current_piece and state != 'game_over':
            shape = game.current_piece["shape"]
            px = game.current_piece["x"]
            py = game.current_piece["y"]
            piece_color = block_color(game.current_piece.get("gold", 0),
                                      game.current_piece.get("color_id", 1),
                                      fallback=(0, 120, 255))

            for r_idx, row in enumerate(shape):
                for c_idx, val in enumerate(row):
                    if val and py + r_idx >= 0:
                        rect = pygame.Rect(board_x + (px + c_idx) * block_size,
                                           board_y + (py + r_idx) * block_size,
                                           block_size - 1, block_size - 1)
                        pygame.draw.rect(screen, piece_color, rect)

        player_label = f"Spēlētājs: {username}" + (" (bezsaistē)" if offline_mode else "")
        draw_text(player_label, 20, 10)
        draw_text(f"Punkti: {game.score}", 20, 35)
        draw_text(f"Līmenis (1-5): {game.level}", 20, 60)

        # Paātrinājuma indikators
        if stress_level > 0:
            ratio = stress_level / STRESS_MAX_STEPS
            warn_color = (255, int(200 - 150 * ratio), 0)
            draw_text(f"Paātrinājums: +{stress_level}", 250, 38, warn_color, 22)

        draw_text("Bultiņas: Kustība/Griezt | P: Pauze", 20, 600)

        if state == 'pause':
            overlay = pygame.Surface((400, 640))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            draw_text("PAUZE", 160, 180, (255, 255, 0), 32)
            draw_text("[P] Turpināt spēli", 70, 250, (255, 255, 255), 20)
            draw_text("[M] Atgriezties izvēlnē", 70, 290, GOLD_COLOR, 20)
            draw_text("[L] Atvērt vietni", 70, 330, (0, 204, 255), 20)
            draw_text("[Q] Iziet no spēles", 70, 370, (255, 100, 100), 20)

        elif state == 'game_over':
            overlay = pygame.Surface((400, 640))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            draw_text("SPĒLE BEIGUSIES", 95, 170, (255, 0, 0))
            draw_text(f"Tavs rezultāts: {game.score}", 105, 215, (255, 255, 255))

            draw_text("[1] Spēlēt no jauna", 50, 280, (255, 255, 255), 22)
            draw_text("[2] Paskatīties līderu tabulu", 50, 320, GOLD_COLOR, 22)
            draw_text("[3] Atvērt vietni (Browser)", 50, 360, (0, 204, 255), 22)
            draw_text("[B] Atgriezties izvēlnē", 50, 400, (200, 200, 200), 22)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
