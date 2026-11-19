"""Seeded benchmarking suite for comparing 2048 AI agents."""

import os
import random
import statistics
import sys
import time
from pathlib import Path

# Allow running both `python -m src.experiments` and `python src/experiments.py`
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents import GreedyAgent, RandomAgent
from board import Board
from expectimax import ExpectimaxAgent


def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


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
    """Interactive CLI benchmark comparing Random, Greedy, and Expectimax on fixed seeds."""
    _clear_screen()
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


if __name__ == "__main__":
    compare_agents()
