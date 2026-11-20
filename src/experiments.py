"""Seeded benchmarking suite, CSV exporter, and Matplotlib chart generator for 2048 AI.

Run headlessly from the repository root to reproduce all report tables and figures:
    python src/experiments.py --games 50 --seed 42
"""

import argparse
import csv
import os
import random
import statistics
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from agents import GreedyAgent, RandomAgent
from board import Board
from cli_utils import ask, clear_screen, pause
from expectimax import ExpectimaxAgent

ROOT_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT_DIR / "outputs" / "results"
FIGURES_DIR = ROOT_DIR / "outputs" / "figures"

AGENT_LABELS = {
    "random": "Random",
    "greedy": "Greedy (D1)",
    "expectimax_d2": "Expectimax (D2)",
    "expectimax_d3": "Expectimax (D3)",
}

def _make_agent(agent_key, seed):
    """Instantiate an agent by key with an isolated RNG seed."""
    if agent_key == "random":
        return RandomAgent(seed=seed)
    if agent_key == "greedy":
        return GreedyAgent(seed=seed)
    if agent_key == "expectimax_d2":
        return ExpectimaxAgent(seed=seed, depth=2)
    if agent_key == "expectimax_d3":
        return ExpectimaxAgent(seed=seed, depth=3)
    raise ValueError(f"Unknown agent key: {agent_key}")

def _play_single_game(args):
    """Run one complete seeded game and return its metrics dict."""
    agent_key, seed = args
    board = Board(random.Random(seed))
    agent = _make_agent(agent_key, seed)
    moves = 0
    start = time.process_time()
    while (move := agent.choose_move(board)) is not None:
        board.step(move)
        moves += 1
    return {
        "seed": seed,
        "score": board.score,
        "max_tile": board.max_tile(),
        "moves": moves,
        "avg_nodes": agent.avg_nodes_per_move(),
        "time_s": time.process_time() - start,
    }

def _print_progress(label, done, total, wall_start):
    """Display live completion count, elapsed time, and ETA on one terminal line."""
    elapsed = time.perf_counter() - wall_start
    eta = (elapsed / done) * (total - done)
    msg = f"  {label}: {done}/{total} games | elapsed: {elapsed:.0f}s | ETA: {eta:.0f}s"
    print(f"{msg:<68s}", end="\r", flush=True)

def run_games(agent_key, n_games, base_seed=42, workers=None, show_progress=False, label=""):
    """Play n_games seeded with base_seed + i, optionally in parallel across CPU cores."""
    tasks = [(agent_key, base_seed + i) for i in range(n_games)]
    max_workers = workers if workers is not None else max(1, (os.cpu_count() or 2) - 1)
    max_workers = min(max_workers, n_games)

    results = []
    wall_start = time.perf_counter()

    if max_workers <= 1:
        for done, task in enumerate(tasks, 1):
            results.append(_play_single_game(task))
            if show_progress:
                _print_progress(label, done, n_games, wall_start)
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(_play_single_game, task) for task in tasks]
            for done, fut in enumerate(as_completed(futures), 1):
                results.append(fut.result())
                if show_progress:
                    _print_progress(label, done, n_games, wall_start)

    if show_progress:
        print(" " * 68, end="\r", flush=True)

    results.sort(key=lambda r: r["seed"])
    return results

def summarize(label, results):
    """Compute summary statistics for one agent's batch of games."""
    n = len(results)
    scores = [r["score"] for r in results]
    tiles = [r["max_tile"] for r in results]
    return {
        "agent": label,
        "games": n,
        "avg_score": round(statistics.mean(scores), 2),
        "std_score": round(statistics.stdev(scores) if n > 1 else 0.0, 2),
        "median_score": round(statistics.median(scores), 2),
        "avg_max_tile": round(statistics.mean(tiles), 2),
        "best_tile": max(tiles),
        "pct_1024_plus": round(100.0 * sum(t >= 1024 for t in tiles) / n, 1),
        "pct_2048_plus": round(100.0 * sum(t >= 2048 for t in tiles) / n, 1),
        "avg_moves": round(statistics.mean(r["moves"] for r in results), 1),
        "avg_nodes": round(statistics.mean(r["avg_nodes"] for r in results), 2),
        "avg_time_s": round(statistics.mean(r["time_s"] for r in results), 3),
    }

def save_csv_outputs(all_results, summaries):
    """Write per-game and summary benchmark tables to outputs/results/."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    per_game_path = RESULTS_DIR / "per_game_results.csv"
    with per_game_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["agent", "seed", "score", "max_tile", "moves", "avg_nodes", "time_s"]
        )
        writer.writeheader()
        for label, results in all_results.items():
            for r in results:
                writer.writerow({"agent": label, **r})

    summary_path = RESULTS_DIR / "summary_table.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)

    return per_game_path, summary_path

def generate_charts(all_results, summaries, n_games, base_seed):
    """Generate the three labelled Matplotlib charts in outputs/figures/."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(
            "Matplotlib is required to generate charts. Install it with: pip install matplotlib"
        ) from exc

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    labels = [s["agent"] for s in summaries]
    colors = ["#8d99ae", "#f4a261", "#2a9d8f", "#264653"][: len(labels)]

    # --- Chart 1: Bar Chart (Average Final Score +/- 1 SD) ---
    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=150)
    avg_scores = [s["avg_score"] for s in summaries]
    std_scores = [s["std_score"] for s in summaries]
    bars = ax.bar(
        labels, avg_scores, yerr=std_scores, capsize=5,
        color=colors, edgecolor="#333333", width=0.55,
    )
    ax.set_title(
        f"Average Final Score by Agent ({n_games} Seeded Games, Base Seed = {base_seed})",
        fontsize=12, fontweight="bold", pad=14,
    )
    ax.set_xlabel("Agent Configuration", fontsize=10, labelpad=8)
    ax.set_ylabel("Average Final Score (+/- 1 SD)", fontsize=10, labelpad=8)
    ax.grid(axis="y", linestyle="--", alpha=0.45)
    ax.set_axisbelow(True)
    top_y = max(a + s for a, s in zip(avg_scores, std_scores))
    ax.set_ylim(0, top_y * 1.24 if top_y > 0 else 100)
    for bar, avg, std, s_row in zip(bars, avg_scores, std_scores, summaries):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            avg + std + top_y * 0.03,
            f"{avg:,.0f}\n(Best: {s_row['best_tile']})",
            ha="center", va="bottom", fontsize=9, fontweight="bold",
        )
    fig.tight_layout()
    fig1_path = FIGURES_DIR / "fig1_avg_score_bar.png"
    fig.savefig(fig1_path)
    plt.close(fig)

    # --- Chart 2: Box Plot (Final Score Distribution across Games) ---
    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=150)
    score_lists = [[r["score"] for r in all_results[lbl]] for lbl in labels]
    bp = ax.boxplot(
        score_lists,
        patch_artist=True,
        showmeans=True,
        meanprops={
            "marker": "D", "markerfacecolor": "white",
            "markeredgecolor": "#222222", "markersize": 5,
        },
        medianprops={"color": "#111111", "linewidth": 1.8},
    )
    ax.set_xticklabels(labels)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
    ax.set_title(
        f"Final Score Distribution Across Agents ({n_games} Seeded Games)",
        fontsize=12, fontweight="bold", pad=14,
    )
    ax.set_xlabel("Agent Configuration", fontsize=10, labelpad=8)
    ax.set_ylabel("Final Game Score", fontsize=10, labelpad=8)
    ax.grid(axis="y", linestyle="--", alpha=0.45)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig2_path = FIGURES_DIR / "fig2_score_distribution_boxplot.png"
    fig.savefig(fig2_path)
    plt.close(fig)

    # --- Chart 3: Line Chart (Performance vs. Search Cost across Depth) ---
    fig, ax1 = plt.subplots(figsize=(8.5, 5.2), dpi=150)
    x = list(range(len(labels)))
    avg_nodes = [s["avg_nodes"] for s in summaries]

    l1 = ax1.plot(x, avg_scores, marker="o", linewidth=2.2, color="#2a9d8f", label="Average Score")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_xlabel("Agent Complexity (Search Depth)", fontsize=10, labelpad=8)
    ax1.set_ylabel("Average Final Score", fontsize=10, color="#2a9d8f", labelpad=8)
    ax1.tick_params(axis="y", labelcolor="#2a9d8f")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    ax2 = ax1.twinx()
    l2 = ax2.plot(
        x, avg_nodes, marker="s", linestyle="--", linewidth=2.0,
        color="#e76f51", label="Avg Nodes / Move (log)",
    )
    ax2.set_yscale("log")
    ax2.set_ylabel("Average Nodes Expanded per Move (log scale)", fontsize=10, color="#e76f51", labelpad=8)
    ax2.tick_params(axis="y", labelcolor="#e76f51")

    lines = l1 + l2
    ax1.legend(lines, [ln.get_label() for ln in lines], loc="upper left", frameon=True)
    ax1.set_title(
        "Performance vs. Search Cost Across Agent Depth",
        fontsize=12, fontweight="bold", pad=14,
    )
    fig.tight_layout()
    fig3_path = FIGURES_DIR / "fig3_performance_vs_nodes_line.png"
    fig.savefig(fig3_path)
    plt.close(fig)

    return fig1_path, fig2_path, fig3_path

def run_benchmark(n_games=50, base_seed=42, include_depth3=True, workers=None,
                  save_outputs=True, make_charts=True):
    """Run the full seeded comparison, print the summary table, and save outputs."""
    keys = ["random", "greedy", "expectimax_d2"]
    if include_depth3:
        keys.append("expectimax_d3")

    eff_workers = workers if workers is not None else max(1, (os.cpu_count() or 2) - 1)
    print(f"Running {n_games} seeded games per agent (base_seed={base_seed}, workers={eff_workers})...\n")

    header = (
        f"{'Agent':18s} {'Avg Score':>10s} {'Std Score':>10s} "
        f"{'Avg Tile':>9s} {'Best':>6s} {'%>=1024':>8s} {'Avg Nodes':>10s} {'CPU/Gm':>8s}"
    )
    print(header)
    print("-" * len(header))

    all_results = {}
    summaries = []
    batch_start = time.perf_counter()

    for key in keys:
        label = AGENT_LABELS[key]
        show_prog = key in ("expectimax_d2", "expectimax_d3")
        results = run_games(
            key, n_games, base_seed=base_seed, workers=workers,
            show_progress=show_prog, label=label,
        )
        all_results[label] = results
        s = summarize(label, results)
        summaries.append(s)
        print(
            f"{s['agent']:18s} {s['avg_score']:10.0f} {s['std_score']:10.0f} "
            f"{s['avg_max_tile']:9.0f} {s['best_tile']:6d} {s['pct_1024_plus']:7.1f}% "
            f"{s['avg_nodes']:10.1f} {s['avg_time_s']:7.2f}s"
        )

    print(f"\nHighest Tile Distribution across {n_games} games:")
    for label, results in all_results.items():
        counts = Counter(r["max_tile"] for r in results)
        dist = ", ".join(f"{tile}: {n} ({n / n_games:.0%})" for tile, n in sorted(counts.items()))
        print(f"  {label:18s} -> {dist}")

    print(f"\nTotal wall-clock time: {time.perf_counter() - batch_start:.1f}s")

    if save_outputs:
        per_game_csv, summary_csv = save_csv_outputs(all_results, summaries)
        print(f"Saved CSVs:   {per_game_csv.relative_to(ROOT_DIR)}, {summary_csv.relative_to(ROOT_DIR)}")
    if make_charts:
        figs = generate_charts(all_results, summaries, n_games, base_seed)
        print("Saved charts: " + ", ".join(str(p.relative_to(ROOT_DIR)) for p in figs))

    return all_results, summaries

def compare_agents():
    """Interactive wrapper called from main.py Menu Option 4."""
    clear_screen()
    print("=== Benchmark Comparison (Fixed Seed = 42) ===")
    n_games = ask("Number of games per agent [default 50]: ", 50, int)
    if n_games < 1:
        n_games = 50
    inc_d3 = input("Include Expectimax Depth-3 in batch run? (y/N): ").strip().lower() == "y"
    print()
    run_benchmark(
        n_games=n_games, base_seed=42, include_depth3=inc_d3,
        save_outputs=True, make_charts=True,
    )
    pause()

def main():
    """Headless CLI entry point for reproducing report benchmarks and charts."""
    parser = argparse.ArgumentParser(description="Run seeded 2048 AI benchmarks and generate charts.")
    parser.add_argument("--games", type=int, default=50, help="Games per agent (default: 50)")
    parser.add_argument("--seed", type=int, default=42, help="Base RNG seed (default: 42)")
    parser.add_argument("--workers", type=int, default=None, help="Parallel worker processes (default: CPU-1)")
    parser.add_argument("--no-depth3", action="store_true", help="Skip Expectimax Depth-3 for quick tests")
    parser.add_argument("--no-charts", action="store_true", help="Skip Matplotlib chart generation")
    args = parser.parse_args()

    if args.games < 1:
        raise SystemExit("--games must be at least 1.")

    try:
        run_benchmark(
            n_games=args.games,
            base_seed=args.seed,
            include_depth3=not args.no_depth3,
            workers=args.workers,
            save_outputs=True,
            make_charts=not args.no_charts,
        )
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user.")

if __name__ == "__main__":
    main()