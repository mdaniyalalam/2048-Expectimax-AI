"""CLI entry point for playing 2048, watching AI agents, and running benchmarks."""

import os
import random
import sys
import time
from pathlib import Path

# Allow running both `python -m src.main` and `python src/main.py`
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents import GreedyAgent
from board import KEYS, Board
from expectimax import ExpectimaxAgent
from experiments import compare_agents
from heuristics import HeuristicEvaluator


def clear_screen():
    """Clear the terminal screen across Windows and Unix platforms."""
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
    """Render the board state and optional status text to the console."""
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
    """Watch an AI agent play a full 2048 game live in the terminal."""
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
    """Prompt the user for Expectimax depth and weights, then watch it play."""
    clear_screen()
    print("=== Configure Expectimax AI ===")
    print("Choose search depth (number of full player turns ahead):")
    print("  1 = Depth-1 (Immediate heuristic evaluation)")
    print("  2 = Depth-2 (Recommended: Fast and strong)")
    print("  3 = Depth-3 (Deep lookahead: stronger but slower)")
    try:
        depth_str = input("Enter depth [default 2]: ").strip()
        depth = int(depth_str) if depth_str else 2
        if depth < 1 or depth > 3:
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


def main():
    """Main interactive CLI menu loop."""
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
