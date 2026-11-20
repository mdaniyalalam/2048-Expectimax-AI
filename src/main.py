"""CLI entry point for playing 2048, watching AI agents, and running benchmarks."""

import time
from agents import GreedyAgent
from board import KEYS, Board
from cli_utils import ask, clear_screen, pause
from expectimax import ExpectimaxAgent
from experiments import compare_agents
from heuristics import HeuristicEvaluator

MENU = """=== 2048 AI with Expectimax (CLI) ===
1) Play it yourself
2) Watch the Greedy AI (Depth-1) play
3) Watch the Expectimax AI (Depth-2 / Depth-3) play
4) Benchmark: Compare Random vs Greedy vs Expectimax (Seeded)
q) Quit"""

DEFAULT_WEIGHTS = {"w_corner": 1.0, "w_empty": 2.0, "w_mono": 1.0, "w_smooth": 0.5}

def evaluation_line(board, evaluator):
    """One line showing the four heuristics and the total utility of a board."""
    c = evaluator.components(board)
    return (
        f"Evaluation  corner: {c['corner']:.1f}   empty: {c['empty']:.0f}   "
        f"mono: {c['mono']:.1f}   smooth: {c['smooth']:.1f}   "
        f"=> utility: {evaluator.evaluate(board):.1f}"
    )

def show(board, extra=""):
    """Render the board and optional status text to the console."""
    clear_screen()
    print(f"2048    Score: {board.score}    Biggest tile: {board.max_tile()}")
    print("-" * 32)
    print(board)
    print("-" * 32)
    if extra:
        print(extra)

def play_yourself():
    """Interactive human play loop using w/a/s/d controls."""
    board = Board()
    evaluator = HeuristicEvaluator()
    while not board.is_game_over():
        show(
            board,
            evaluation_line(board, evaluator)
            + "\nMove with w/a/s/d then press Enter.  q = quit to menu",
        )
        key = input("> ").strip().lower()
        if key == "q":
            return
        if key in KEYS:
            board.step(KEYS[key])
    show(board, "GAME OVER!")
    pause()

def watch_ai(agent=None, delay=0.05):
    """Watch an AI agent play a full 2048 game live in the terminal."""
    board = Board()
    agent = agent or GreedyAgent()
    evaluator = getattr(agent, "evaluator", HeuristicEvaluator())
    moves = 0
    start = time.perf_counter()

    while (move := agent.choose_move(board)) is not None:
        board.step(move)
        moves += 1
        show(
            board,
            f"{agent.name} is playing...  moves: {moves}   "
            f"nodes (last move): {agent.nodes_expanded}   "
            f"avg nodes/move: {agent.avg_nodes_per_move():.1f}   "
            f"time: {time.perf_counter() - start:.1f}s   (Ctrl+C to stop)\n"
            + evaluation_line(board, evaluator),
        )
        time.sleep(delay)

    show(
        board,
        f"GAME OVER after {moves} moves!  Final Score: {board.score}  "
        f"Max Tile: {board.max_tile()}  Avg Nodes/Move: {agent.avg_nodes_per_move():.1f}",
    )
    pause()

def configure_and_watch_expectimax():
    """Prompt for Expectimax depth and weights, then watch it play."""
    clear_screen()
    print("=== Configure Expectimax AI ===")
    print("Choose search depth (number of full player turns ahead):")
    print("  1 = Depth-1 (Immediate heuristic evaluation)")
    print("  2 = Depth-2 (Recommended: Fast and strong)")
    print("  3 = Depth-3 (Deep lookahead: stronger but slower)")
    depth = ask("Enter depth [default 2]: ", 2, int)
    if not 1 <= depth <= 3:
        print("Invalid depth. Using default depth = 2.")
        depth = 2

    weights = dict(DEFAULT_WEIGHTS)
    print("\nDefaults: " + ", ".join(f"{k}={v}" for k, v in weights.items()))
    if input("Customize weights? (y/N): ").strip().lower() == "y":
        weights = {name: ask(f"  {name} [{value}]: ", value, float) for name, value in weights.items()}

    watch_ai(ExpectimaxAgent(depth=depth, **weights), delay=0.02 if depth == 2 else 0.0)

def main():
    """Main interactive CLI menu loop."""
    actions = {
        "1": play_yourself,
        "2": lambda: watch_ai(GreedyAgent()),
        "3": configure_and_watch_expectimax,
        "4": compare_agents,
    }
    while True:
        clear_screen()
        print(MENU)
        try:
            choice = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if choice == "q":
            break
        try:
            if choice in actions:
                actions[choice]()
        except (EOFError, KeyboardInterrupt):
            pass

if __name__ == "__main__":
    main()
