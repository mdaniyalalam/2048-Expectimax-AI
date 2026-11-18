import math
import os
import random
import statistics
import time

SIZE = 4
DIRECTIONS = ["left", "right", "up", "down"]
KEYS = {"a": "left", "d": "right", "w": "up", "s": "down"}


# ----------------------------------------------------------------------
# 1. THE GAME (Environment / State)
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

    # Proposal Section 4.1 alias methods so both naming conventions work seamlessly
    def move(self, direction):
        """Alias for step(direction) matching Proposal Section 4.1."""
        return self.step(direction)

    def get_valid_moves(self):
        """Alias for legal_moves() matching Proposal Section 4.1."""
        return self.legal_moves()

    def spawn_tile(self):
        """Alias for add_tile() matching Proposal Section 4.1."""
        self.add_tile()

    def __str__(self):
        lines = []
        for row in self.grid:
            lines.append(" ".join(f"{v:5d}" if v else "    ." for v in row))
        return "\n".join(lines)


# Alias Board2048 -> Board to match Proposal Section 4.1 class naming
Board2048 = Board


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
        return (
            self.w_corner * c["corner"]
            + self.w_empty * c["empty"]
            + self.w_mono * c["mono"]
            + self.w_smooth * c["smooth"]
        )


# ----------------------------------------------------------------------
# 3. THE PLAYERS (AIs)
# ----------------------------------------------------------------------
class Agent:
    """Base class for all players. Each one must implement choose_move()."""

    name = "Agent"

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.nodes_expanded = 0
        self.total_nodes_expanded = 0
        self.moves_made = 0

    def choose_move(self, board):
        """Return the direction to play on this board."""
        raise NotImplementedError("Subclasses must implement choose_move")

    def select_move(self, board):
        """Alias for choose_move() matching Proposal Section 4.1."""
        return self.choose_move(board)

    def avg_nodes_per_move(self):
        """Average search tree nodes expanded per move over the agent's lifetime."""
        return self.total_nodes_expanded / self.moves_made if self.moves_made > 0 else 0.0


# Alias BaseAgent -> Agent to match Proposal Section 4.1 class naming
BaseAgent = Agent


class RandomAgent(Agent):
    """Baseline: picks any legal move at random."""

    name = "Random"

    def choose_move(self, board):
        legal = board.legal_moves()
        if not legal:
            return None
        self.nodes_expanded = 1
        self.total_nodes_expanded += 1
        self.moves_made += 1
        return self.rng.choice(legal)


class GreedyAgent(Agent):
    """Depth-1 baseline: tries every move and picks the one whose resulting board
    has the best heuristic utility. It looks only at the board right after the
    slide, before any new tile appears, so it never plans for the random spawn."""

    name = "Greedy (depth-1 heuristic)"

    def __init__(self, seed=None, evaluator=None):
        super().__init__(seed)
        self.evaluator = evaluator if evaluator is not None else HeuristicEvaluator()

    def choose_move(self, board):
        legal = board.legal_moves()
        if not legal:
            return None
        self.nodes_expanded = 0
        best_moves, best_score = [], -math.inf
        for move in legal:
            trial = board.copy()
            trial.slide(move)                          # try it on a copy, not the real board
            self.nodes_expanded += 1
            score = self.evaluator.evaluate(trial)     # <- the "evaluation": how good is this board?
            if score > best_score:
                best_moves, best_score = [move], score
            elif score == best_score:
                best_moves.append(move)

        self.total_nodes_expanded += self.nodes_expanded
        self.moves_made += 1
        return self.rng.choice(best_moves)             # break ties randomly


class ExpectimaxAgent(Agent):
    """Expectimax Search Agent for 2048.

    Alternates between:
      - MAX nodes (is_player_turn=True): Player chooses a directional slide
        (left, right, up, down) to maximize expected heuristic utility.
      - CHANCE nodes (is_player_turn=False): Environment spawns a '2' (p=0.9)
        or a '4' (p=0.1) uniformly across available empty cells.

    Depth Design:
      `depth` measures FULL player turns (plies of player actions).
      - depth = 1: Evaluates the board right after the player's first slide.
      - depth = 2: Player slide -> Chance tile spawn -> Player response slide -> Evaluate.
      - depth = 3: 3 player s lides interleaved with 2 chance spawn layers.
    """

    PROB_2 = 0.9
    PROB_4 = 0.1

    def __init__(
        self,
        seed=None,
        depth=2,
        evaluator=None,
        w_corner=1.0,
        w_empty=2.0,
        w_mono=1.0,
        w_smooth=0.5,
        max_chance_branches=None,
    ):
        super().__init__(seed)
        if depth < 1:
            raise ValueError("Expectimax depth must be at least 1.")
        self.depth = depth

        if evaluator is not None:
            self.evaluator = evaluator
        else:
            self.evaluator = HeuristicEvaluator(
                w_corner=w_corner,
                w_empty=w_empty,
                w_mono=w_mono,
                w_smooth=w_smooth,
            )

        # Keep direct weight attributes in sync with Proposal Section 4.1
        self.w_corner = self.evaluator.w_corner
        self.w_empty = self.evaluator.w_empty
        self.w_mono = self.evaluator.w_mono
        self.w_smooth = self.evaluator.w_smooth

        # Optional cap on empty cells sampled at chance nodes (mitigates Depth-3 slowdown
        # when the board has many empty cells, as described in Proposal Section 10).
        if max_chance_branches is not None:
            self.max_chance_branches = max_chance_branches
        else:
            self.max_chance_branches = 6 if depth >= 3 else None

        self.name = f"Expectimax (depth-{self.depth})"

    def set_depth(self, new_depth):
        """Dynamically update the search depth."""
        if new_depth < 1:
            raise ValueError("Expectimax depth must be at least 1.")
        self.depth = new_depth
        if self.max_chance_branches is None and new_depth >= 3:
            self.max_chance_branches = 6
        self.name = f"Expectimax (depth-{self.depth})"

    def set_weights(self, w_corner, w_empty, w_mono, w_smooth):
        """Dynamically update the four heuristic weights."""
        self.w_corner = w_corner
        self.w_empty = w_empty
        self.w_mono = w_mono
        self.w_smooth = w_smooth
        self.evaluator.w_corner = w_corner
        self.evaluator.w_empty = w_empty
        self.evaluator.w_mono = w_mono
        self.evaluator.w_smooth = w_smooth

    def evaluate(self, board):
        """Evaluate a leaf board state using the heuristic evaluator."""
        return self.evaluator.evaluate(board)

    def expectimax(self, board, depth, is_player_turn):
        """Recursive Expectimax search.

        Parameters:
            board (Board): Current simulated 4x4 board state.
            depth (int): Remaining player turns to search.
            is_player_turn (bool): True for MAX node (player slide),
                                   False for CHANCE node (random tile spawn).

        Returns:
            float: Expected heuristic utility of the state.
        """
        self.nodes_expanded += 1

        # Base case: search horizon reached
        if depth == 0:
            return self.evaluate(board)

        if is_player_turn:
            # ---------------- MAX NODE (Player Turn) ----------------
            best_score = -math.inf
            any_legal_move = False

            for direction in DIRECTIONS:
                child = board.copy()
                if not child.slide(direction):
                    continue
                any_legal_move = True

                # If depth == 1, we evaluate immediately after the player's last planned move
                # rather than expanding another chance layer that has no subsequent player move.
                if depth == 1:
                    self.nodes_expanded += 1
                    score = self.evaluate(child)
                else:
                    score = self.expectimax(child, depth - 1, is_player_turn=False)

                if score > best_score:
                    best_score = score

            # Terminal state check: no valid directional slide exists
            if not any_legal_move:
                return self.evaluate(board)

            return best_score

        else:
            # ---------------- CHANCE NODE (Environment Tile Spawn) ----------------
            empty = board.empty_cells()
            if not empty:
                return self.expectimax(board, depth, is_player_turn=True)

            # If a branch cap is active (e.g., at Depth 3 when the board is very open),
            # sample a subset of empty cells to keep real-time search responsive.
            if self.max_chance_branches is not None and len(empty) > self.max_chance_branches:
                empty = self.rng.sample(empty, self.max_chance_branches)

            expected_utility = 0.0
            cell_prob = 1.0 / len(empty)

            for r, c in empty:
                # Branch 1: A '2' spawns in (r, c) with probability 0.9
                board.grid[r][c] = 2
                u2 = self.expectimax(board, depth, is_player_turn=True)

                # Branch 2: A '4' spawns in (r, c) with probability 0.1
                board.grid[r][c] = 4
                u4 = self.expectimax(board, depth, is_player_turn=True)

                # Restore empty cell in-place (avoids 2*N full board copies per chance node)
                board.grid[r][c] = 0

                expected_utility += cell_prob * (self.PROB_2 * u2 + self.PROB_4 * u4)

            return expected_utility

    def choose_move(self, board):
        """Evaluate all legal root moves using Expectimax and return the best direction."""
        self.nodes_expanded = 0
        best_moves = []
        best_score = -math.inf

        for direction in DIRECTIONS:
            trial = board.copy()
            if not trial.slide(direction):
                continue

            if self.depth == 1:
                self.nodes_expanded += 1
                score = self.evaluate(trial)
            else:
                score = self.expectimax(trial, self.depth - 1, is_player_turn=False)

            if score > best_score:
                best_moves = [direction]
                best_score = score
            elif score == best_score:
                best_moves.append(direction)

        if not best_moves:
            return None

        self.total_nodes_expanded += self.nodes_expanded
        self.moves_made += 1
        return self.rng.choice(best_moves)


# ----------------------------------------------------------------------
# 4. THE MENU & BENCHMARK SUITE
# ----------------------------------------------------------------------
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def evaluation_line(board, evaluator):
    """One line showing the four heuristics and the total utility of a board."""
    c = evaluator.components(board)
    return (
        f"Evaluation  corner: {c['corner']:.1f}   empty: {c['empty']:.0f}   "
        f"mono: {c['mono']:.1f}   smooth: {c['smooth']:.1f}   "
        f"=> utility: {evaluator.evaluate(board):.1f}"
    )


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
        show(
            board,
            evaluation_line(board, evaluator)
            + "\nMove with w/a/s/d then press Enter.  q = quit to menu",
        )
        try:
            key = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if key == "q":
            return
        if key in KEYS:
            board.step(KEYS[key])
    show(board, "GAME OVER!")
    try:
        input("Press Enter to go back to the menu...")
    except (EOFError, KeyboardInterrupt):
        return


def watch_ai(agent=None, delay=0.05):
    board = Board(random.Random())
    agent = agent if agent is not None else GreedyAgent()
    evaluator = getattr(agent, "evaluator", HeuristicEvaluator())
    moves = 0
    start_time = time.perf_counter()

    while not board.is_game_over():
        move = agent.choose_move(board)
        if move is None:
            break
        board.step(move)
        moves += 1
        elapsed = time.perf_counter() - start_time
        extra_info = (
            f"{agent.name} is playing...  moves: {moves}   "
            f"nodes (last move): {agent.nodes_expanded}   "
            f"avg nodes/move: {agent.avg_nodes_per_move():.1f}   "
            f"time: {elapsed:.1f}s   (Ctrl+C to stop)\n"
            + evaluation_line(board, evaluator)
        )
        show(board, extra_info)
        if delay > 0:
            time.sleep(delay)

    show(
        board,
        f"GAME OVER after {moves} moves!  Final Score: {board.score}  "
        f"Max Tile: {board.max_tile()}  Avg Nodes/Move: {agent.avg_nodes_per_move():.1f}",
    )
    try:
        input("Press Enter to go back to the menu...")
    except (EOFError, KeyboardInterrupt):
        return


def configure_and_watch_expectimax():
    clear_screen()
    print("=== Configure Expectimax AI ===")
    print("Choose search depth (number of full player turns ahead):")
    print("  1 = Depth-1 (Immediate heuristic evaluation)")
    print("  2 = Depth-2 (Recommended: Fast and strong)")
    print("  3 = Depth-3 (Deep lookahead: stronger but slower)")
    try:
        depth_str = input("Enter depth [default 2]: ").strip()
        depth = int(depth_str) if depth_str else 2
        if depth < 1 or depth > 4:
            print("Invalid depth. Using default depth = 2.")
            depth = 2
    except ValueError:
        print("Invalid input. Using default depth = 2.")
        depth = 2

    print("\nCustomize heuristic weights? (Press Enter to keep defaults)")
    print("Defaults: w_corner=1.0, w_empty=2.0, w_mono=1.0, w_smooth=0.5")
    try:
        custom = input("Customize weights? (y/N): ").strip().lower()
        if custom == "y":
            w_corner = float(input("  w_corner [1.0]: ").strip() or 1.0)
            w_empty = float(input("  w_empty  [2.0]: ").strip() or 2.0)
            w_mono = float(input("  w_mono   [1.0]: ").strip() or 1.0)
            w_smooth = float(input("  w_smooth [0.5]: ").strip() or 0.5)
        else:
            w_corner, w_empty, w_mono, w_smooth = 1.0, 2.0, 1.0, 0.5
    except ValueError:
        print("Invalid number entered. Reverting to default weights.")
        w_corner, w_empty, w_mono, w_smooth = 1.0, 2.0, 1.0, 0.5

    agent = ExpectimaxAgent(
        depth=depth,
        w_corner=w_corner,
        w_empty=w_empty,
        w_mono=w_mono,
        w_smooth=w_smooth,
    )
    delay = 0.02 if depth == 2 else 0.0
    watch_ai(agent=agent, delay=delay)


def run_games(agent_factory, n_games, base_seed=42):
    """Play n_games with one agent type. Same seeds => fair, repeatable comparison.

    `agent_factory` can be an Agent class (like RandomAgent) or a callable
    `lambda seed: ExpectimaxAgent(seed=seed, depth=2)`.
    Returns a list of dicts with detailed per-game metrics.
    """
    results = []
    for i in range(n_games):
        game_seed = base_seed + i
        board = Board(random.Random(game_seed))   # identical initial boards & tile spawns
        agent = agent_factory(game_seed)
        moves = 0
        t0 = time.perf_counter()
        while not board.is_game_over():
            move = agent.choose_move(board)
            if move is None:
                break
            board.step(move)
            moves += 1
        elapsed = time.perf_counter() - t0
        results.append(
            {
                "score": board.score,
                "max_tile": board.max_tile(),
                "moves": moves,
                "avg_nodes": agent.avg_nodes_per_move(),
                "time_s": elapsed,
            }
        )
    return results


def compare_agents():
    clear_screen()
    print("=== Benchmark Comparison (Fixed Seed = 42) ===")
    try:
        n_str = input("Number of games per agent [default 50]: ").strip()
        n_games = int(n_str) if n_str else 50
        if n_games < 1:
            n_games = 50
    except ValueError:
        n_games = 50

    try:
        inc_d3 = input("Include Expectimax Depth-3 in batch run? (y/N): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    agent_configs = [
        ("Random", lambda seed: RandomAgent(seed=seed)),
        ("Greedy (depth-1 heuristic)", lambda seed: GreedyAgent(seed=seed)),
        ("Expectimax (depth-2)", lambda seed: ExpectimaxAgent(seed=seed, depth=2)),
    ]
    if inc_d3 == "y":
        agent_configs.append(
            ("Expectimax (depth-3)", lambda seed: ExpectimaxAgent(seed=seed, depth=3))
        )

    print(f"\nPlaying {n_games} seeded games per agent (base_seed=42)...\n")
    header = (
        f"{'Player':28s} {'Avg Score':>10s} {'Std Score':>10s} "
        f"{'Avg MaxTile':>12s} {'Best Tile':>10s} {'Avg Nodes/Mv':>13s} {'Avg Time/Gm':>12s}"
    )
    print(header)
    print("-" * len(header))

    all_tile_counts = {}
    for label, factory in agent_configs:
        results = run_games(factory, n_games, base_seed=42)
        scores = [r["score"] for r in results]
        tiles = [r["max_tile"] for r in results]
        nodes = [r["avg_nodes"] for r in results]
        times = [r["time_s"] for r in results]

        avg_score = statistics.mean(scores)
        std_score = statistics.stdev(scores) if len(scores) > 1 else 0.0
        avg_tile = statistics.mean(tiles)
        best_tile = max(tiles)
        avg_nodes = statistics.mean(nodes)
        avg_time = statistics.mean(times)

        print(
            f"{label:28s} {avg_score:10.0f} {std_score:10.0f} "
            f"{avg_tile:12.0f} {best_tile:10d} {avg_nodes:13.1f} {avg_time:11.2f}s"
        )

        # Count how often each max tile was reached
        dist = {}
        for t in tiles:
            dist[t] = dist.get(t, 0) + 1
        all_tile_counts[label] = dist

    print("\nHighest Tile Distribution across", n_games, "games:")
    for label, dist in all_tile_counts.items():
        sorted_tiles = ", ".join(
            f"{tile}: {count} ({count / n_games * 100:.0f}%)"
            for tile, count in sorted(dist.items())
        )
        print(f"  {label:28s} -> {sorted_tiles}")

    try:
        input("\nPress Enter to go back to the menu...")
    except (EOFError, KeyboardInterrupt):
        return


def main():
    while True:
        clear_screen()
        print("=== 2048 AI with Expectimax (CLI) ===")
        print("1) Play it yourself")
        print("2) Watch the Greedy AI (Depth-1) play")
        print("3) Watch the Expectimax AI (Depth-2 / Depth-3) play")
        print("4) Benchmark: Compare Random vs Greedy vs Expectimax (Seeded)")
        print("q) Quit")
        try:
            choice = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "1":
            play_yourself()
        elif choice == "2":
            try:
                watch_ai(agent=GreedyAgent())
            except KeyboardInterrupt:
                pass
        elif choice == "3":
            try:
                configure_and_watch_expectimax()
            except KeyboardInterrupt:
                pass
        elif choice == "4":
            try:
                compare_agents()
            except KeyboardInterrupt:
                pass
        elif choice == "q":
            break


if __name__ == "__main__":
    main()
