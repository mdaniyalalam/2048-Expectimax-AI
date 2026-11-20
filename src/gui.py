"""Pygame graphical interface for the 2048 AI (Expectimax) project.

Two-panel desktop interface:
  - Left: interactive 4x4 board, live score/tile/move counters, and a status bar.
  - Right: agent selector (Human, Random, Greedy, Expectimax), playback controls
    (Play/Pause, Step, Reset, Speed), Expectimax depth and heuristic weight
    controls, and live search/heuristic telemetry.

Run from the repository root:
    python src/gui.py
"""

import time

try:
    import pygame
except ImportError as exc:
    raise SystemExit(
        "Pygame is required to run the GUI. Install it with: pip install pygame"
    ) from exc

from agents import GreedyAgent, RandomAgent
from board import SIZE, Board
from expectimax import ExpectimaxAgent
from heuristics import HeuristicEvaluator

WINDOW_WIDTH = 940
WINDOW_HEIGHT = 640
FPS = 60
BG_COLOR = (250, 248, 239)
CARD_BG = (242, 238, 228)
CARD_BORDER = (214, 205, 196)
BOARD_BG = (187, 173, 160)
TEXT_DARK = (119, 110, 101)
TEXT_MUTED = (143, 132, 121)
TEXT_LIGHT = (249, 246, 242)
ACCENT_ORANGE = (237, 140, 89)
ACCENT_ORANGE_HOVER = (224, 124, 72)
ACCENT_GREEN = (98, 168, 124)
ACCENT_GREEN_HOVER = (82, 150, 108)
BTN_BG = (224, 216, 204)
BTN_HOVER = (209, 199, 185)
BTN_ACTIVE = (143, 122, 102)
BTN_DISABLED = (233, 228, 220)
TEXT_DISABLED = (185, 178, 170)

# Tile value -> (background, text) colors
TILE_COLORS = {
    0: ((205, 193, 180), TEXT_DARK),
    2: ((238, 228, 218), TEXT_DARK),
    4: ((237, 224, 200), TEXT_DARK),
    8: ((242, 177, 121), TEXT_LIGHT),
    16: ((245, 149, 99), TEXT_LIGHT),
    32: ((246, 124, 95), TEXT_LIGHT),
    64: ((246, 94, 59), TEXT_LIGHT),
    128: ((237, 207, 114), TEXT_LIGHT),
    256: ((237, 204, 97), TEXT_LIGHT),
    512: ((237, 200, 80), TEXT_LIGHT),
    1024: ((237, 197, 63), TEXT_LIGHT),
    2048: ((237, 194, 46), TEXT_LIGHT),
}
TILE_DEFAULT_HIGH = ((60, 58, 50), TEXT_LIGHT)

SPEED_PRESETS = {"Slow": 0.25, "Normal": 0.06, "Fast": 0.005}
DEFAULT_WEIGHTS = {"w_corner": 1.0, "w_empty": 2.0, "w_mono": 1.0, "w_smooth": 0.5}
WEIGHT_ROWS = [
    ("w_corner", "Corner (w_corner)"),
    ("w_empty", "Empty (w_empty)"),
    ("w_mono", "Monotonicity (w_mono)"),
    ("w_smooth", "Smoothness (w_smooth)"),
]
WEIGHT_STEP = 0.25
HUMAN_KEYS = {
    pygame.K_LEFT: "left", pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_DOWN: "down", pygame.K_s: "down",
}


def _font(size, bold=False, name="arial"):
    return pygame.font.SysFont(name, size, bold=bold)

class Button:
    """Clickable rounded button with hover, active, and disabled states."""

    def __init__(self, rect, label, callback, bg=BTN_BG, hover_bg=BTN_HOVER,
                 active_bg=BTN_ACTIVE, small=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.bg, self.hover_bg, self.active_bg = bg, hover_bg, active_bg
        self.small = small
        self.active = False
        self.enabled = True

    def is_clicked(self, pos):
        """True if the button is enabled and contains the click position."""
        return self.enabled and self.rect.collidepoint(pos)

    def draw(self, surface, font, mouse_pos):
        """Render the button."""
        light_text = self.bg in (ACCENT_ORANGE, ACCENT_GREEN)
        if not self.enabled:
            fill, fg = BTN_DISABLED, TEXT_DISABLED
        elif self.active:
            fill, fg = self.active_bg, TEXT_LIGHT
        else:
            hovered = self.rect.collidepoint(mouse_pos)
            fill = self.hover_bg if hovered else self.bg
            fg = TEXT_LIGHT if light_text else TEXT_DARK
        pygame.draw.rect(surface, fill, self.rect, border_radius=6)
        text = font.render(self.label, True, fg)
        surface.blit(text, text.get_rect(center=self.rect.center))

class Game2048GUI:
    """Interactive Pygame application for playing and visualizing 2048 AI agents."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("2048 AI — Expectimax Search")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = _font(34, True)
        self.font_subtitle = _font(13)
        self.font_card_hdr = _font(12, True)
        self.font_stat_lbl = _font(11, True)
        self.font_stat_val = _font(20, True)
        self.font_btn = _font(14, True)
        self.font_btn_sm = _font(12, True)
        self.font_body = _font(14)
        self.font_mono = _font(13, name="consolas")
        self.font_mono_bold = _font(14, True, "consolas")
        self.font_overlay = _font(36, True)
        self.tile_fonts = {n: _font(size, True) for n, size in enumerate((44, 42, 34, 28, 22), 1)}

        self.mode = "Expectimax"
        self.depth = 2
        self.speed_name = "Normal"
        self.evaluator = HeuristicEvaluator(**DEFAULT_WEIGHTS)
        self.board = Board()
        self.moves = 0
        self.last_move = "-"
        self.ai_running = False
        self.step_requested = False
        self.last_ai_step_time = 0.0
        self.agent = self._build_agent()
        self._build_ui()

    def _build_agent(self):
        """Create the agent for the current mode; agents share the GUI's evaluator."""
        if self.mode == "Random":
            return RandomAgent()
        if self.mode == "Greedy":
            return GreedyAgent(evaluator=self.evaluator)
        if self.mode == "Expectimax":
            return ExpectimaxAgent(depth=self.depth, evaluator=self.evaluator)
        return None

    def reset_game(self):
        """Start a fresh board and reset counters."""
        self.board = Board()
        self.moves = 0
        self.last_move = "-"
        self.ai_running = self.step_requested = False
        self.agent = self._build_agent()

    def set_mode(self, new_mode):
        """Switch player mode and stop any running autoplay."""
        if new_mode != self.mode:
            self.mode = new_mode
            self.ai_running = self.step_requested = False
            self.agent = self._build_agent()

    def set_depth(self, new_depth):
        """Update the Expectimax search depth live."""
        self.depth = new_depth
        if isinstance(self.agent, ExpectimaxAgent):
            self.agent.depth = new_depth

    def adjust_weight(self, name, delta):
        """Change a heuristic weight by delta, clamped at 0."""
        setattr(self.evaluator, name, round(max(0.0, getattr(self.evaluator, name) + delta), 2))

    def reset_weights(self):
        """Restore the default heuristic weights."""
        for name, value in DEFAULT_WEIGHTS.items():
            setattr(self.evaluator, name, value)

    def _toggle_play(self):
        if self.mode != "Human" and not self.board.is_game_over():
            self.ai_running = not self.ai_running

    def _apply_move(self, move):
        """Play a move, update counters, and stop autoplay at game over."""
        if move is None or not self.board.step(move):
            return
        self.moves += 1
        self.last_move = move.upper()
        if self.board.is_game_over():
            self.ai_running = False

    def _autoplay(self):
        """Make the AI's next move when playing (after the speed delay) or stepping."""
        if self.mode == "Human" or self.board.is_game_over():
            return
        due = time.perf_counter() - self.last_ai_step_time >= SPEED_PRESETS[self.speed_name]
        if self.step_requested or (self.ai_running and due):
            self.step_requested = False
            self._apply_move(self.agent.choose_move(self.board))
            self.last_ai_step_time = time.perf_counter()

    def _build_ui(self):
        """Create all static rects and buttons."""
        self.board_rect = pygame.Rect(24, 104, 480, 480)
        self.status_rect = pygame.Rect(24, 594, 480, 30)
        self.card_mode = pygame.Rect(528, 24, 388, 114)
        self.card_controls = pygame.Rect(528, 148, 388, 110)
        self.card_params = pygame.Rect(528, 268, 388, 196)
        self.card_telemetry = pygame.Rect(528, 474, 388, 150)

        modes = [("Human", "Human", 540, 54), ("Random", "Random", 728, 54),
                 ("Greedy", "Greedy (D1)", 540, 94), ("Expectimax", "Expectimax", 728, 94)]
        self.mode_buttons = {
            m: Button((x, y, 176, 32), label, lambda m=m: self.set_mode(m))
            for m, label, x, y in modes
        }

        self.btn_play = Button((540, 178, 116, 32), "Play", self._toggle_play,
                               ACCENT_GREEN, ACCENT_GREEN_HOVER, ACCENT_ORANGE)
        self.btn_step = Button((664, 178, 116, 32), "Step",
                               lambda: setattr(self, "step_requested", True))
        self.btn_reset = Button((788, 178, 116, 32), "Reset", self.reset_game,
                                ACCENT_ORANGE, ACCENT_ORANGE_HOVER)

        self.speed_buttons = {
            name: Button((x, 218, 94, 28), name, lambda n=name: setattr(self, "speed_name", n), small=True)
            for name, x in (("Slow", 610), ("Normal", 710), ("Fast", 810))
        }
        self.depth_buttons = {
            d: Button((x, 302, 66, 28), f"D{d}", lambda d=d: self.set_depth(d), small=True)
            for d, x in ((1, 694), (2, 766), (3, 838))
        }

        self.btn_defaults = Button((830, 273, 74, 22), "Defaults", self.reset_weights, small=True)
        self.weight_buttons = []
        for i, (name, _) in enumerate(WEIGHT_ROWS):
            y = 340 + i * 29
            self.weight_buttons += [
                Button((774, y, 28, 24), "-", lambda n=name: self.adjust_weight(n, -WEIGHT_STEP)),
                Button((876, y, 28, 24), "+", lambda n=name: self.adjust_weight(n, WEIGHT_STEP)),
            ]

        self.buttons = [
            *self.mode_buttons.values(), self.btn_play, self.btn_step, self.btn_reset,
            *self.speed_buttons.values(), *self.depth_buttons.values(),
            self.btn_defaults, *self.weight_buttons,
        ]

    def _sync_button_states(self):
        """Update button active/enabled flags to reflect the current state."""
        is_ai = self.mode != "Human"
        game_over = self.board.is_game_over()
        for name, btn in self.mode_buttons.items():
            btn.active = name == self.mode

        self.btn_play.enabled = is_ai and not game_over
        self.btn_play.active = self.ai_running
        self.btn_play.label = "Pause" if self.ai_running else "Play"
        self.btn_step.enabled = is_ai and not self.ai_running and not game_over

        for name, btn in self.speed_buttons.items():
            btn.enabled, btn.active = is_ai, name == self.speed_name
        for d, btn in self.depth_buttons.items():
            btn.enabled, btn.active = self.mode == "Expectimax", d == self.depth

        uses_heuristics = self.mode in ("Greedy", "Expectimax")
        for btn in (self.btn_defaults, *self.weight_buttons):
            btn.enabled = uses_heuristics

    def _handle_keydown(self, key):
        """Handle shortcuts (R, Space) and Human mode directional input."""
        if key == pygame.K_r:
            self.reset_game()
        elif key == pygame.K_SPACE:
            self._toggle_play()
        elif self.mode == "Human" and key in HUMAN_KEYS and not self.board.is_game_over():
            self._apply_move(HUMAN_KEYS[key])

    def _handle_click(self, pos):
        """Run the callback of the clicked button, if any."""
        for btn in self.buttons:
            if btn.is_clicked(pos):
                btn.callback()
                return

    def _text(self, font, text, color, **place):
        """Blit text positioned by pygame Rect keyword arguments (e.g. center=, topleft=)."""
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(**place))

    def _draw_card(self, rect, title):
        pygame.draw.rect(self.screen, CARD_BG, rect, border_radius=8)
        pygame.draw.rect(self.screen, CARD_BORDER, rect, width=1, border_radius=8)
        self._text(self.font_card_hdr, title, TEXT_MUTED, topleft=(rect.x + 12, rect.y + 8))

    def _draw_header(self):
        """Draw the title and Score / Best Tile / Moves boxes."""
        self._text(self.font_title, "2048 AI", TEXT_DARK, topleft=(24, 24))
        self._text(self.font_subtitle, "Expectimax Search Engine", TEXT_MUTED, topleft=(26, 66))
        stats = [("SCORE", self.board.score, 216), ("BEST TILE", self.board.max_tile(), 315),
                 ("MOVES", self.moves, 414)]
        for label, value, x in stats:
            box = pygame.Rect(x, 24, 90, 56)
            pygame.draw.rect(self.screen, BOARD_BG, box, border_radius=6)
            self._text(self.font_stat_lbl, label, (238, 228, 218), centerx=box.centerx, top=box.top + 7)
            self._text(self.font_stat_val, str(value), TEXT_LIGHT, centerx=box.centerx, top=box.top + 24)

    def _draw_board(self):
        """Draw the grid, tiles, and the Game Over overlay."""
        pygame.draw.rect(self.screen, BOARD_BG, self.board_rect, border_radius=10)
        pad = 12
        cell = (self.board_rect.width - pad * (SIZE + 1)) // SIZE
        for r in range(SIZE):
            for c in range(SIZE):
                val = self.board.grid[r][c]
                bg, fg = TILE_COLORS.get(val, TILE_DEFAULT_HIGH)
                rect = pygame.Rect(
                    self.board_rect.x + pad + c * (cell + pad),
                    self.board_rect.y + pad + r * (cell + pad),
                    cell, cell,
                )
                pygame.draw.rect(self.screen, bg, rect, border_radius=6)
                if val:
                    text = str(val)
                    self._text(self.tile_fonts.get(len(text), self.tile_fonts[5]), text, fg, center=rect.center)

        if not self.board.is_game_over():
            return
        overlay = pygame.Surface(self.board_rect.size, pygame.SRCALPHA)
        overlay.fill((250, 248, 239, 195))
        self.screen.blit(overlay, self.board_rect.topleft)
        cx, cy = self.board_rect.center
        lines = [
            (self.font_overlay, "Game Over!", TEXT_DARK, -24),
            (self.font_body, f"Final Score: {self.board.score}   |   Max Tile: {self.board.max_tile()}", TEXT_DARK, 18),
            (self.font_subtitle, "Click Reset or press R to start a new game", TEXT_MUTED, 44),
        ]
        for font, text, color, dy in lines:
            self._text(font, text, color, center=(cx, cy + dy))

    def _draw_status_bar(self):
        pygame.draw.rect(self.screen, CARD_BG, self.status_rect, border_radius=6)
        pygame.draw.rect(self.screen, CARD_BORDER, self.status_rect, width=1, border_radius=6)
        if self.board.is_game_over():
            msg = "Game Over  |  Press R or click Reset to play again"
        elif self.mode == "Human":
            msg = "Human Mode  |  Use Arrow Keys or WASD to slide  |  R: Reset"
        elif self.ai_running:
            msg = f"{self.agent.name} playing ({self.speed_name})  |  Space: Pause"
        else:
            msg = f"{self.agent.name} paused  |  Click Play, Step, or press Space"
        self._text(self.font_subtitle, msg, TEXT_DARK, centery=self.status_rect.centery, left=self.status_rect.x + 12)

    def _draw_right_panel(self, mouse_pos):
        """Draw the Mode, Controls, Parameters, and Telemetry cards."""
        self._draw_card(self.card_mode, "AGENT MODE")
        self._draw_card(self.card_controls, "CONTROLS")
        self._draw_card(self.card_params, "AI PARAMETERS")
        self._draw_card(self.card_telemetry, "LIVE TELEMETRY")
        self._text(self.font_body, "Speed:", TEXT_DARK, topleft=(540, 223))
        self._text(self.font_body, "Search Depth:", TEXT_DARK, topleft=(540, 307))
        
        for i, (name, label) in enumerate(WEIGHT_ROWS):
            y = 340 + i * 29
            self._text(self.font_body, label, TEXT_DARK, topleft=(540, y + 3))
            self._text(self.font_mono_bold, f"{getattr(self.evaluator, name):.2f}", TEXT_DARK, center=(839, y + 12))

        for btn in self.buttons:
            btn.draw(self.screen, self.font_btn_sm if btn.small else self.font_btn, mouse_pos)

        nodes_last = self.agent.nodes_expanded if self.agent else 0
        avg_nodes = self.agent.avg_nodes_per_move() if self.agent else 0.0
        comp = self.evaluator.components(self.board)
        pygame.draw.line(self.screen, CARD_BORDER, (540, 550), (904, 550), 1)
        rows = [
            (self.font_mono, f"Last Move: {self.last_move:<5s}   Nodes (Move): {nodes_last}", TEXT_DARK, 506),
            (self.font_mono, f"Avg Nodes/Move:  {avg_nodes:.1f}", TEXT_DARK, 527),
            (self.font_mono, f"Corner: {comp['corner']:6.1f}     Empty:  {comp['empty']:6.0f}", TEXT_DARK, 558),
            (self.font_mono, f"Mono:   {comp['mono']:6.1f}     Smooth: {comp['smooth']:6.1f}", TEXT_DARK, 579),
            (self.font_mono_bold, f"Weighted Utility: {self.evaluator.evaluate(self.board):7.2f}", ACCENT_ORANGE, 601),
        ]
        for font, text, color, y in rows:
            self._text(font, text, color, topleft=(540, y))

    def run(self):
        """Run the main event, update, and render loop."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)

            self._autoplay()
            self._sync_button_states()
            self.screen.fill(BG_COLOR)
            self._draw_header()
            self._draw_board()
            self._draw_status_bar()
            self._draw_right_panel(pygame.mouse.get_pos())
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

def main():
    """Launch the 2048 AI Pygame interface."""
    Game2048GUI().run()

if __name__ == "__main__":
    main()
