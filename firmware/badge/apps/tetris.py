"""Simple Tetris clone game."""

import time

from apps.base_app import BaseApp
from ui.page import Page
import lvgl
import ui.styles as styles

# Game constants
BOARD_WIDTH = 40
BOARD_HEIGHT = 9  # Visible height (fits in 142px screen)
CELL_SIZE = 10  # pixels
BOARD_X = 10  # Offset from left
BOARD_Y = 0  # Offset from top

# Tetris pieces (shapes defined as offsets from center)
PIECES = {
    'I': [[(-1, 0), (0, 0), (1, 0), (2, 0)]],
    'O': [[(0, 0), (1, 0), (0, 1), (1, 1)]],
    'T': [[(0, -1), (-1, 0), (0, 0), (1, 0)],
          [(0, -1), (0, 0), (0, 1), (1, 0)],
          [(0, -1), (-1, 0), (0, 0), (0, 1)],
          [(0, -1), (-1, 0), (0, 0), (1, 0)]],
    'S': [[(-1, 0), (0, 0), (0, -1), (1, -1)],
          [(0, -1), (0, 0), (1, 0), (1, 1)],
          [(-1, 0), (0, 0), (0, -1), (1, -1)],
          [(0, -1), (0, 0), (1, 0), (1, 1)]],
    'Z': [[(-1, -1), (0, -1), (0, 0), (1, 0)],
          [(0, 0), (1, -1), (0, -1), (1, 0)],
          [(-1, -1), (0, -1), (0, 0), (1, 0)],
          [(0, 0), (1, -1), (0, -1), (1, 0)]],
    'J': [[(-1, -1), (-1, 0), (0, 0), (1, 0)],
          [(0, -1), (1, -1), (0, 0), (0, 1)],
          [(-1, 0), (0, 0), (1, 0), (1, 1)],
          [(0, -1), (0, 0), (-1, 1), (0, 1)]],
    'L': [[(1, -1), (-1, 0), (0, 0), (1, 0)],
          [(0, -1), (0, 0), (0, 1), (1, 1)],
          [(-1, 0), (0, 0), (1, 0), (-1, 1)],
          [(-1, -1), (0, -1), (0, 0), (0, 1)]],
}


class Tetris(BaseApp):
    """Simple Tetris game."""

    def __init__(self, name: str, badge):
        super().__init__(name, badge)
        self.foreground_sleep_ms = 100
        self.board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.current_piece = None
        self.current_x = 0
        self.current_y = 0
        self.current_rotation = 0
        self.fall_time = 0
        self.fall_interval = 500  # milliseconds
        self.score = 0
        self.game_over = False
        self.piece_colors = {
            'I': 0x00FFFF, 'O': 0xFFFF00, 'T': 0x800080, 'S': 0x00FF00,
            'Z': 0xFF0000, 'J': 0x0000FF, 'L': 0xFFA500
        }
        self.block_objects = []
        self.page = None

    def new_piece(self):
        """Spawn a new random piece."""
        import random
        piece_type = random.choice(list(PIECES.keys()))
        self.current_piece = piece_type
        self.current_x = BOARD_WIDTH // 2
        self.current_y = 0
        self.current_rotation = 0
        if self.check_collision():
            self.game_over = True

    def get_piece_cells(self):
        """Get absolute positions of current piece cells."""
        if not self.current_piece:
            return []
        rotations = PIECES[self.current_piece]
        shape = rotations[self.current_rotation % len(rotations)]
        cells = []
        for dx, dy in shape:
            x = self.current_x + dx
            y = self.current_y + dy
            if 0 <= y < BOARD_HEIGHT:
                cells.append((x, y))
        return cells

    def check_collision(self, dx=0, dy=0, rotation=None):
        """Check if piece collides with board or walls."""
        if not self.current_piece:
            return True
        rotations = PIECES[self.current_piece]
        rot = rotation if rotation is not None else self.current_rotation
        shape = rotations[rot % len(rotations)]
        
        for dx_shape, dy_shape in shape:
            x = self.current_x + dx + dx_shape
            y = self.current_y + dy + dy_shape
            
            # Check walls
            if x < 0 or x >= BOARD_WIDTH:
                return True
            if y >= BOARD_HEIGHT:
                return True
            # Check board
            if y >= 0 and self.board[y][x] != 0:
                return True
        return False

    def lock_piece(self):
        """Lock current piece to board."""
        if not self.current_piece:
            return
        cells = self.get_piece_cells()
        color = self.piece_colors[self.current_piece]
        for x, y in cells:
            if 0 <= y < BOARD_HEIGHT and 0 <= x < BOARD_WIDTH:
                self.board[y][x] = color
        self.clear_lines()
        self.new_piece()

    def clear_lines(self):
        """Clear full lines and drop remaining blocks."""
        lines_cleared = 0
        y = BOARD_HEIGHT - 1
        while y >= 0:
            if all(self.board[y][x] != 0 for x in range(BOARD_WIDTH)):
                # Line is full, remove it
                del self.board[y]
                self.board.insert(0, [0] * BOARD_WIDTH)
                lines_cleared += 1
                # Don't decrement y since lines above shifted down
            else:
                y -= 1
        self.score += lines_cleared * 100

    def move_left(self):
        """Move piece left."""
        if not self.check_collision(dx=-1):
            self.current_x -= 1
            return True
        return False

    def move_right(self):
        """Move piece right."""
        if not self.check_collision(dx=1):
            self.current_x += 1
            return True
        return False

    def move_down(self):
        """Move piece down."""
        if not self.check_collision(dy=1):
            self.current_y += 1
            return True
        return False

    def rotate(self):
        """Rotate piece."""
        if not self.current_piece:
            return False
        new_rotation = (self.current_rotation + 1) % len(PIECES[self.current_piece])
        if not self.check_collision(rotation=new_rotation):
            self.current_rotation = new_rotation
            return True
        return False

    def draw_board(self):
        """Draw the game board."""
        if not self.page:
            return
        
        # Clear old blocks
        for obj in self.block_objects:
            obj.delete()
        self.block_objects = []
        
        # Draw locked blocks
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                if self.board[y][x] != 0:
                    block = lvgl.obj(self.page.content)
                    block.set_size(CELL_SIZE - 1, CELL_SIZE - 1)
                    block.set_style_bg_color(lvgl.color_hex(self.board[y][x]), 0)
                    block.set_style_border_width(0, 0)
                    block.align(lvgl.ALIGN.TOP_LEFT, 
                               BOARD_X + x * CELL_SIZE, 
                               BOARD_Y + y * CELL_SIZE)
                    self.block_objects.append(block)
        
        # Draw current piece
        if self.current_piece and not self.game_over:
            color = self.piece_colors[self.current_piece]
            cells = self.get_piece_cells()
            for x, y in cells:
                if 0 <= y < BOARD_HEIGHT:
                    block = lvgl.obj(self.page.content)
                    block.set_size(CELL_SIZE - 1, CELL_SIZE - 1)
                    block.set_style_bg_color(lvgl.color_hex(color), 0)
                    block.set_style_border_width(0, 0)
                    block.align(lvgl.ALIGN.TOP_LEFT,
                               BOARD_X + x * CELL_SIZE,
                               BOARD_Y + y * CELL_SIZE)
                    self.block_objects.append(block)
        
        # Draw board border
        border = lvgl.obj(self.page.content)
        border.set_size(BOARD_WIDTH * CELL_SIZE + 2, BOARD_HEIGHT * CELL_SIZE + 2)
        border.set_style_bg_opa(0, 0)
        border.set_style_border_width(1, 0)
        border.set_style_border_color(styles.lcd_color_fg, 0)
        border.align(lvgl.ALIGN.TOP_LEFT, BOARD_X - 1, BOARD_Y - 1)
        self.block_objects.append(border)

    def start(self):
        super().start()

    def run_foreground(self):
        """Run game loop."""
        if self.game_over:
            # Allow restart with any F key
            if self.badge.keyboard.f1() or self.badge.keyboard.f2() or \
               self.badge.keyboard.f3() or self.badge.keyboard.f4():
                self.reset_game()
                return
            if self.badge.keyboard.f5():
                self.switch_to_background()
            return
        
        # Handle input
        key = self.badge.keyboard.read_key()
        moved = False
        
        if key == self.badge.keyboard.LEFT:
            self.move_left()
            moved = True
        elif key == self.badge.keyboard.RIGHT:
            self.move_right()
            moved = True
        elif key == self.badge.keyboard.DOWN:
            if self.move_down():
                self.fall_time = time.ticks_ms()
            moved = True
        elif key == self.badge.keyboard.UP:
            self.rotate()
            moved = True
        
        # Auto-fall
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.fall_time) >= self.fall_interval:
            if not self.move_down():
                self.lock_piece()
            self.fall_time = current_time
        
        # Redraw
        self.draw_board()
        
        # Update score display
        if self.page:
            try:
                score_label = getattr(self, '_score_label', None)
                if score_label:
                    score_label.set_text(f"Score: {self.score}")
                else:
                    score_label = lvgl.label(self.page.content)
                    score_label.set_text(f"Score: {self.score}")
                    score_label.align(lvgl.ALIGN.TOP_LEFT, BOARD_X + BOARD_WIDTH * CELL_SIZE + 10, BOARD_Y)
                    self._score_label = score_label
                
                # Show game over message
                if self.game_over:
                    game_over_label = getattr(self, '_game_over_label', None)
                    if not game_over_label:
                        game_over_label = lvgl.label(self.page.content)
                        game_over_label.set_text("GAME OVER\nPress F1-F4\nto restart")
                        game_over_label.set_style_text_align(lvgl.TEXT_ALIGN.CENTER, 0)
                        game_over_label.align(lvgl.ALIGN.CENTER, 0, 0)
                        game_over_label.set_style_bg_opa(lvgl.OPA.COVER, 0)
                        game_over_label.set_style_bg_color(styles.hackaday_grey, 0)
                        self._game_over_label = game_over_label
            except:
                pass
        
        if self.badge.keyboard.f5():
            self.switch_to_background()

    def reset_game(self):
        """Reset game state."""
        self.board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.game_over = False
        self.fall_time = time.ticks_ms()
        # Clear game over label if it exists
        if self.page:
            game_over_label = getattr(self, '_game_over_label', None)
            if game_over_label:
                try:
                    game_over_label.delete()
                except:
                    pass
                self._game_over_label = None
        self.new_piece()

    def run_background(self):
        super().run_background()

    def switch_to_foreground(self):
        """Initialize game display."""
        super().switch_to_foreground()
        self.page = Page()
        self.page.create_infobar(["Tetris", "Score: 0"])
        self.page.create_content()
        self.page.create_menubar(["← Left", "→ Right", "↓ Down", "↑ Rotate", "Exit"])
        self.page.replace_screen()
        
        # Initialize game
        self.fall_time = time.ticks_ms()
        if not self.current_piece:
            self.new_piece()
        self.draw_board()

    def switch_to_background(self):
        """Clean up when switching to background."""
        # Clear block objects
        for obj in self.block_objects:
            try:
                obj.delete()
            except:
                pass
        self.block_objects = []
        self.page = None
        super().switch_to_background()

