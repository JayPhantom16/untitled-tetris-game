<<<<<<< HEAD
import random
import time

class TetrisGame:
    def __init__(self):
        self.width = 10
        self.height = 20
        # Glabāsim katrā šūnā vārdnīcu vai sarakstu: [color_id, is_gold, lock_time]
        self.board = [[None]*self.width for _ in range(self.height)]
        self.score = 0
        self.level = 1
        self.game_over = False
        self.time_since_last_clear = 0  
        self.current_piece = self.new_piece()
        
    def new_piece(self):
        is_gold = 1 if random.random() < 0.2 else 0
        shapes = [
            {"shape": [[1, 1, 1, 1]], "color_id": 1},      # Gaismas zils
            {"shape": [[1, 1], [1, 1]], "color_id": 2},      # Oranžš
            {"shape": [[0, 1, 0], [1, 1, 1]], "color_id": 3},# Violetš
            {"shape": [[1, 0, 0], [1, 1, 1]], "color_id": 4},# Zaļš
            {"shape": [[0, 0, 1], [1, 1, 1]], "color_id": 5} # Sarkans
        ]
        chosen = random.choice(shapes)
        return {
            "shape": chosen["shape"], 
            "x": 3, 
            "y": 0, 
            "gold": is_gold, 
            "color_id": chosen["color_id"]
        }

    def update_difficulty(self):
        # Vismaz 5 līmeņi atkarībā no punktiem
        if self.score > 1000:
            self.level = 5
        elif self.score > 700:
            self.level = 4
        elif self.score > 400:
            self.level = 3
        elif self.score > 200:
            self.level = 2
        else:
            self.level = 1

    def rotate_piece(self):
        shape = self.current_piece["shape"]
        rotated = [list(row) for row in zip(*shape[::-1])]
        old_shape = self.current_piece["shape"]
        self.current_piece["shape"] = rotated
        if self.check_collision():
            self.current_piece["shape"] = old_shape

    def check_collision(self):
        shape = self.current_piece["shape"]
        px = self.current_piece["x"]
        py = self.current_piece["y"]
        
        for r_idx, row in enumerate(shape):
            for c_idx, val in enumerate(row):
                if val:
                    b_y = py + r_idx
                    b_x = px + c_idx
                    if b_x < 0 or b_x >= self.width or b_y >= self.height:
                        return True
                    if b_y >= 0 and self.board[b_y][b_x] is not None:
                        return True
        return False

    def lock_piece(self):
        shape = self.current_piece["shape"]
        px = self.current_piece["x"]
        py = self.current_piece["y"]
        is_gold = self.current_piece.get("gold", 0)
        color_id = self.current_piece.get("color_id", 1)
        
        current_time = time.time()
        
        for r_idx, row in enumerate(shape):
            for c_idx, val in enumerate(row):
                if val:
                    board_y = py + r_idx
                    board_x = px + c_idx
                    if 0 <= board_y < self.height and 0 <= board_x < self.width:
                        # Saglabājam datus: (color_id, is_gold, fiksēšanas laiks)
                        self.board[board_y][board_x] = {
                            "color_id": 9 if is_gold else color_id,
                            "is_gold": is_gold,
                            "lock_time": current_time
                        }
                        
        self.clear_lines()
        self.current_piece = self.new_piece()
        
        if self.check_collision():
            self.game_over = True

    def update_gold_status(self):
        # Pārbauda un atjaunina zelta blokus, ja pagājušas vismaz 10 sekundes
        current_time = time.time()
        for r_idx, row in enumerate(self.board):
            for c_idx, cell in enumerate(row):
                if cell is not None and cell["is_gold"] == 1:
                    # Ja pagājušas vismaz 10 sekundes kopš fiksēšanas
                    if current_time - cell["lock_time"] >= 10:
                        cell["is_gold"] = 0
                        cell["color_id"] = 1  # Maina krāsu uz parasto (piem., gaismas zilu)

    def clear_lines(self):
        self.update_gold_status()
        lines_to_clear = [i for i, row in enumerate(self.board) if all(cell is not None for cell in row)]
        
        if lines_to_clear:
            for i in lines_to_clear:
                # Ja rindā ir zelta bloks, kas vēl nav zaudējis statusu, dod papildus +100 punktus
                has_active_gold = any(cell["is_gold"] == 1 for cell in self.board[i] if cell is not None)
                base_points = 100
                bonus_points = 100 if has_active_gold else 0
                
                del self.board[i]
                self.board.insert(0, [None]*self.width)
                self.score += (base_points + bonus_points)
                
            self.time_since_last_clear = 0
        else:
            self.time_since_last_clear += 1
            if self.time_since_last_clear > 20:
                self.score = max(0, self.score - 5)
        
=======
import random
import time

class TetrisGame:
    def __init__(self):
        self.width = 10
        self.height = 20
        # Glabāsim katrā šūnā vārdnīcu vai sarakstu: [color_id, is_gold, lock_time]
        self.board = [[None]*self.width for _ in range(self.height)]
        self.score = 0
        self.level = 1
        self.game_over = False
        self.time_since_last_clear = 0  
        self.current_piece = self.new_piece()
        
    def new_piece(self):
        is_gold = 1 if random.random() < 0.2 else 0
        shapes = [
            {"shape": [[1, 1, 1, 1]], "color_id": 1},      # Gaismas zils
            {"shape": [[1, 1], [1, 1]], "color_id": 2},      # Oranžš
            {"shape": [[0, 1, 0], [1, 1, 1]], "color_id": 3},# Violetš
            {"shape": [[1, 0, 0], [1, 1, 1]], "color_id": 4},# Zaļš
            {"shape": [[0, 0, 1], [1, 1, 1]], "color_id": 5} # Sarkans
        ]
        chosen = random.choice(shapes)
        return {
            "shape": chosen["shape"], 
            "x": 3, 
            "y": 0, 
            "gold": is_gold, 
            "color_id": chosen["color_id"]
        }

    def update_difficulty(self):
        # Vismaz 5 līmeņi atkarībā no punktiem
        if self.score > 1000:
            self.level = 5
        elif self.score > 700:
            self.level = 4
        elif self.score > 400:
            self.level = 3
        elif self.score > 200:
            self.level = 2
        else:
            self.level = 1

    def rotate_piece(self):
        shape = self.current_piece["shape"]
        rotated = [list(row) for row in zip(*shape[::-1])]
        old_shape = self.current_piece["shape"]
        self.current_piece["shape"] = rotated
        if self.check_collision():
            self.current_piece["shape"] = old_shape

    def check_collision(self):
        shape = self.current_piece["shape"]
        px = self.current_piece["x"]
        py = self.current_piece["y"]
        
        for r_idx, row in enumerate(shape):
            for c_idx, val in enumerate(row):
                if val:
                    b_y = py + r_idx
                    b_x = px + c_idx
                    if b_x < 0 or b_x >= self.width or b_y >= self.height:
                        return True
                    if b_y >= 0 and self.board[b_y][b_x] is not None:
                        return True
        return False

    def lock_piece(self):
        shape = self.current_piece["shape"]
        px = self.current_piece["x"]
        py = self.current_piece["y"]
        is_gold = self.current_piece.get("gold", 0)
        color_id = self.current_piece.get("color_id", 1)
        
        current_time = time.time()
        
        for r_idx, row in enumerate(shape):
            for c_idx, val in enumerate(row):
                if val:
                    board_y = py + r_idx
                    board_x = px + c_idx
                    if 0 <= board_y < self.height and 0 <= board_x < self.width:
                        # Saglabājam datus: (color_id, is_gold, fiksēšanas laiks)
                        self.board[board_y][board_x] = {
                            "color_id": 9 if is_gold else color_id,
                            "is_gold": is_gold,
                            "lock_time": current_time
                        }
                        
        self.clear_lines()
        self.current_piece = self.new_piece()
        
        if self.check_collision():
            self.game_over = True

    def update_gold_status(self):
        # Pārbauda un atjaunina zelta blokus, ja pagājušas vismaz 10 sekundes
        current_time = time.time()
        for r_idx, row in enumerate(self.board):
            for c_idx, cell in enumerate(row):
                if cell is not None and cell["is_gold"] == 1:
                    # Ja pagājušas vismaz 10 sekundes kopš fiksēšanas
                    if current_time - cell["lock_time"] >= 10:
                        cell["is_gold"] = 0
                        cell["color_id"] = 1  # Maina krāsu uz parasto (piem., gaismas zilu)

    def clear_lines(self):
        self.update_gold_status()
        lines_to_clear = [i for i, row in enumerate(self.board) if all(cell is not None for cell in row)]
        
        if lines_to_clear:
            for i in lines_to_clear:
                # Ja rindā ir zelta bloks, kas vēl nav zaudējis statusu, dod papildus +100 punktus
                has_active_gold = any(cell["is_gold"] == 1 for cell in self.board[i] if cell is not None)
                base_points = 100
                bonus_points = 100 if has_active_gold else 0
                
                del self.board[i]
                self.board.insert(0, [None]*self.width)
                self.score += (base_points + bonus_points)
                
            self.time_since_last_clear = 0
        else:
            self.time_since_last_clear += 1
            if self.time_since_last_clear > 20:
                self.score = max(0, self.score - 5)
        
>>>>>>> b8fdab76fa7ba2f49bb8fb796cf5ebd7d484c39e
        self.update_difficulty()