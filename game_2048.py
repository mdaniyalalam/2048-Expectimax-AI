import math
import os
import random
import time

SIZE = 4
DIRECTIONS = ["left", "right", "up", "down"]
KEYS = {"a": "left", "d": "right", "w": "up", "s": "down"}


# ----------------------------------------------------------------------
# 1. THE GAME
# ----------------------------------------------------------------------
class Board:
    """A 4x4 2048 board. 0 means an empty cell."""

    def __init__(self, rng=None):
        # rng = a random number generator. Giving it a seed makes games repeatable.
        self.rng = rng if rng is not None else random.Random()
        self.grid = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self.add_tile()
        self.add_tile()

    def copy(self):
        """Make an independent copy (used by AIs to 'try' a move safely)."""
        other = Board.__new__(Board)
        other.rng = self.rng
        other.grid = [row[:] for row in self.grid]
        other.score = self.score
        return other

    def empty_cells(self):
        """List of (row, col) positions that are empty."""
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if self.grid[r][c] == 0]

    def add_tile(self):
        """Put a 2 (90% of the time) or a 4 (10%) on a random empty cell."""
        cells = self.empty_cells()
        if not cells:
            return
        r, c = self.rng.choice(cells)
        self.grid[r][c] = 2 if self.rng.random() < 0.9 else 4

    @staticmethod
    def _slide_row_left(row):
        """Slide one row to the left and merge equal neighbours.
        Returns (new_row, points_gained)."""
        tiles = [v for v in row if v != 0]       # drop the zeros: [2,0,2,4] -> [2,2,4]
        merged, gained, i = [], 0, 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                merged.append(tiles[i] * 2)      # two equal tiles become one
                gained += tiles[i] * 2
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        merged += [0] * (SIZE - len(merged))     # fill the rest with zeros
        return merged, gained

    def slide(self, direction):
        """Slide the whole board. Does NOT add a new tile.
        Returns True if anything moved, False if the move did nothing."""
        before = [row[:] for row in self.grid]
        g = self.grid
        if direction == "left":
            lines = g
        elif direction == "right":
            lines = [row[::-1] for row in g]
        elif direction == "up":
            lines = [list(col) for col in zip(*g)]
        elif direction == "down":
            lines = [list(col)[::-1] for col in zip(*g)]
        else:
            raise ValueError(f"Unknown direction: {direction}")

        new_lines = []
        for line in lines:
            new_line, gained = self._slide_row_left(line)
            self.score += gained
            new_lines.append(new_line)

        # undo the flipping we did to reuse the "left" logic
        if direction == "left":
            self.grid = new_lines
        elif direction == "right":
            self.grid = [row[::-1] for row in new_lines]
        elif direction == "up":
            self.grid = [list(row) for row in zip(*new_lines)]
        elif direction == "down":
            self.grid = [list(row) for row in zip(*[line[::-1] for line in new_lines])]

        return self.grid != before

    def step(self, direction):
        """A real turn: slide, and if something moved, a new tile appears."""
        moved = self.slide(direction)
        if moved:
            self.add_tile()
        return moved

    def legal_moves(self):
        """Directions that would actually change the board."""
        return [d for d in DIRECTIONS if self.copy().slide(d)]

    def is_game_over(self):
        """True when no direction changes the board (no empty cell and no merge)."""
        return len(self.legal_moves()) == 0

    def max_tile(self):
        """Value of the biggest tile on the board."""
        return max(max(row) for row in self.grid)

    def __str__(self):
        lines = []
        for row in self.grid:
            lines.append(" ".join(f"{v:5d}" if v else "    ." for v in row))
        return "\n".join(lines)


# ----------------------------------------------------------------------
# 2. THE EVALUATION FUNCTION (4 heuristics, adjustable weights)
# ----------------------------------------------------------------------
class HeuristicEvaluator:
    """Scores a board from 'how good does this look for the player?'.
    Higher = better. The utility is a weighted sum of four heuristics:

      corner      biggest tile sits in a corner          
      empty       number of empty cells                  
      monotonic   rows/columns that only go up or down  
      smooth      neighbouring tiles have similar values 

    Tile values are converted with log2 (2->1, 4->2, 8->3 ...) so that a huge tile
    does not drown out everything else."""

    def __init__(self, w_corner=1.0, w_empty=2.0, w_mono=1.0, w_smooth=0.5):
        self.w_corner = w_corner
        self.w_empty = w_empty
        self.w_mono = w_mono
        self.w_smooth = w_smooth

    @staticmethod
    def _log(value):
        """log2 of a tile value; empty cells count as 0."""
        return math.log2(value) if value > 0 else 0.0

    def corner_score(self, board):
        """log2(max tile) if a biggest tile is in a corner, otherwise 0."""
        g, last = board.grid, SIZE - 1
        corners = (g[0][0], g[0][last], g[last][0], g[last][last])
        biggest = board.max_tile()
        return self._log(biggest) if biggest in corners else 0.0

    def empty_score(self, board):
        """Number of empty cells (0 to 16)."""
        return float(len(board.empty_cells()))

    def monotonicity_score(self, board):
        """Minus the total amount by which rows and columns break a steady
        increase or decrease. 0 means all 8 lines are perfectly monotonic."""
        g = board.grid
        lines = [row for row in g] + [list(col) for col in zip(*g)]
        penalty = 0.0
        for line in lines:
            vals = [self._log(v) for v in line]
            up = down = 0.0
            for a, b in zip(vals, vals[1:]):
                if a > b:
                    down += a - b        # line is going down here
                else:
                    up += b - a          # line is going up here
            penalty += min(up, down)     # cost of the less-followed direction
        return -penalty

    def smoothness_score(self, board):
        """Minus the sum of log-differences between touching non-empty tiles."""
        g = board.grid
        total = 0.0
        for r in range(SIZE):
            for c in range(SIZE):
                if g[r][c] == 0:
                    continue
                here = self._log(g[r][c])
                if c + 1 < SIZE and g[r][c + 1] != 0:
                    total += abs(here - self._log(g[r][c + 1]))
                if r + 1 < SIZE and g[r + 1][c] != 0:
                    total += abs(here - self._log(g[r + 1][c]))
        return -total

    def components(self, board):
        """The four raw heuristic values (before weighting), as a dict."""
        return {
            "corner": self.corner_score(board),
            "empty": self.empty_score(board),
            "mono": self.monotonicity_score(board),
            "smooth": self.smoothness_score(board),
        }

    def evaluate(self, board):
        """The utility of a board: weighted sum of the four heuristics."""
        c = self.components(board)
        return (self.w_corner * c["corner"] + self.w_empty * c["empty"]
                + self.w_mono * c["mono"] + self.w_smooth * c["smooth"])


# ----------------------------------------------------------------------
# 3. THE PLAYERS (AIs)
# ----------------------------------------------------------------------
class Agent:
    """Base class for all players. Each one must implement choose_move()."""

    name = "Agent"

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def choose_move(self, board):
        """Return the direction to play on this board."""
        raise NotImplementedError("Subclasses must implement choose_move")


class RandomAgent(Agent):
    """Baseline: picks any legal move at random."""

    name = "Random"

    def choose_move(self, board):
        return self.rng.choice(board.legal_moves())


class GreedyAgent(Agent):
    """Depth-1 baseline: tries every move and picks the one whose resulting board
    has the best heuristic utility. It looks only at the board right after the
    slide, before any new tile appears, so it never plans for the random spawn."""

    name = "Greedy (depth-1 heuristic)"

    def __init__(self, seed=None, evaluator=None):
        super().__init__(seed)
        self.evaluator = evaluator if evaluator is not None else HeuristicEvaluator()

    def choose_move(self, board):
        best_moves, best_score = [], -math.inf
        for move in board.legal_moves():
            trial = board.copy()
            trial.slide(move)                          # try it on a copy, not the real board
            score = self.evaluator.evaluate(trial)     # <- the "evaluation": how good is this board?
            if score > best_score:
                best_moves, best_score = [move], score
            elif score == best_score:
                best_moves.append(move)
        return self.rng.choice(best_moves)             # break ties randomly


# ----------------------------------------------------------------------
# 4. THE MENU
# ----------------------------------------------------------------------
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def evaluation_line(board, evaluator):
    """One line showing the four heuristics and the total utility of a board."""
    c = evaluator.components(board)
    return (f"Evaluation  corner: {c['corner']:.1f}   empty: {c['empty']:.0f}   "
            f"mono: {c['mono']:.1f}   smooth: {c['smooth']:.1f}   "
            f"=> utility: {evaluator.evaluate(board):.1f}")


def show(board, extra=""):
    clear_screen()
    print(f"2048    Score: {board.score}    Biggest tile: {board.max_tile()}")
    print("-" * 32)
    print(board)
    print("-" * 32)
    if extra:
        print(extra)


def play_yourself():
    board = Board()
    evaluator = HeuristicEvaluator()
    while not board.is_game_over():
        show(board, evaluation_line(board, evaluator)
             + "\nMove with w/a/s/d then press Enter.  q = quit to menu")
        key = input("> ").strip().lower()
        if key == "q":
            return
        if key in KEYS:
            board.step(KEYS[key])
    show(board, "GAME OVER!")
    input("Press Enter to go back to the menu...")


def watch_ai(agent=None):
    board = Board(random.Random())
    agent = agent if agent is not None else GreedyAgent()
    evaluator = HeuristicEvaluator()
    moves = 0
    while not board.is_game_over():
        board.step(agent.choose_move(board))
        moves += 1
        show(board, f"{agent.name} is playing...  moves: {moves}   (Ctrl+C to stop)\n"
             + evaluation_line(board, evaluator))
        time.sleep(0.05)
    show(board, f"GAME OVER after {moves} moves.")
    input("Press Enter to go back to the menu...")


def run_games(agent_class, n_games, base_seed):
    """Play n_games with one agent type. Same seeds => fair, repeatable comparison."""
    results = []
    for i in range(n_games):
        board = Board(random.Random(base_seed + i))   # same boards for every agent
        agent = agent_class(seed=base_seed + i)
        while not board.is_game_over():
            board.step(agent.choose_move(board))
        results.append((board.score, board.max_tile()))
    return results


def compare_agents():
    n_games = 50
    print(f"\nPlaying {n_games} games per player (this can take a few seconds)...\n")
    print(f"{'Player':28s} {'Avg score':>10s} {'Avg max tile':>13s} {'Best tile':>10s}")
    for agent_class in (RandomAgent, GreedyAgent):
        results = run_games(agent_class, n_games, base_seed=42)
        avg_score = sum(s for s, _ in results) / n_games
        avg_tile = sum(t for _, t in results) / n_games
        best_tile = max(t for _, t in results)
        print(f"{agent_class.name:28s} {avg_score:10.0f} {avg_tile:13.0f} {best_tile:10d}")
    input("\nPress Enter to go back to the menu...")


def main():
    while True:
        clear_screen()
        print("=== 2048 starter ===")
        print("1) Play it yourself")
        print("2) Watch the Greedy AI play")
        print("3) Compare Random vs Greedy over 50 games")
        print("q) Quit")
        choice = input("> ").strip().lower()
        if choice == "1":
            play_yourself()
        elif choice == "2":
            try:
                watch_ai()
            except KeyboardInterrupt:
                pass
        elif choice == "3":
            compare_agents()
        elif choice == "q":
            break


if __name__ == "__main__":
    main()
