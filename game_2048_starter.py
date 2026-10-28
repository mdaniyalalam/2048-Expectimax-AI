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
        return len(self.legal_moves()) == 0

    def max_tile(self):
        return max(max(row) for row in self.grid)

    def __str__(self):
        lines = []
        for row in self.grid:
            lines.append(" ".join(f"{v:5d}" if v else "    ." for v in row))
        return "\n".join(lines)


# ----------------------------------------------------------------------
# 2. THE PLAYERS (AIs)
# ----------------------------------------------------------------------
class Agent:
    """Base class for all players. Each one must implement choose_move()."""

    name = "Agent"

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def choose_move(self, board):
        raise NotImplementedError("Subclasses must implement choose_move")


class RandomAgent(Agent):
    """Baseline: picks any legal move at random."""

    name = "Random"

    def choose_move(self, board):
        return self.rng.choice(board.legal_moves())


class GreedyAgent(Agent):
    """First tiny AI: tries every move and picks the one that leaves the most
    empty cells (more empty space = more room to survive)."""

    name = "Greedy (most empty cells)"

    def choose_move(self, board):
        best_moves, best_score = [], -1
        for move in board.legal_moves():
            trial = board.copy()
            trial.slide(move)                    # try it on a copy, not the real board
            score = len(trial.empty_cells())     # <- the "evaluation": how good is this board?
            if score > best_score:
                best_moves, best_score = [move], score
            elif score == best_score:
                best_moves.append(move)
        return self.rng.choice(best_moves)       # break ties randomly


# ----------------------------------------------------------------------
# 3. THE MENU
# ----------------------------------------------------------------------
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


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
    while not board.is_game_over():
        show(board, "Move with w/a/s/d then press Enter.  q = quit to menu")
        key = input("> ").strip().lower()
        if key == "q":
            return
        if key in KEYS:
            board.step(KEYS[key])
    show(board, "GAME OVER!")
    input("Press Enter to go back to the menu...")


def watch_ai():
    board = Board(random.Random())
    agent = GreedyAgent()
    moves = 0
    while not board.is_game_over():
        board.step(agent.choose_move(board))
        moves += 1
        show(board, f"{agent.name} is playing...  moves: {moves}   (Ctrl+C to stop)")
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
