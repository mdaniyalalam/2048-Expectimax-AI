# 2048 AI — Expectimax Search Engine

An intelligent game-playing agent for the stochastic 4×4 puzzle game **2048**, implemented from scratch in modular Python for **AL-2002 Artificial Intelligence (Lab)** at FAST-NUCES Karachi (Fall 2026). The system models 2048 as a stochastic decision environment and uses **Expectimax search** (alternating MAX player turns and probabilistic CHANCE tile-spawn nodes) paired with a four-component `log2`-scaled heuristic evaluation function (Corner, Empty Cells, Monotonicity, and Smoothness). It includes an interactive Pygame GUI, a console interface, and a seeded multi-core benchmarking suite that evaluates Random, Greedy (Depth-1), Expectimax (Depth-2), and Expectimax (Depth-3) agents across reproducible runs.

---

## Author & Contribution

* **Muhammad Daniyal Alam (`24K-2048`)** — *Solo Project*: Designed and implemented the complete system, including the 2048 game engine (`board.py`), heuristic evaluation function (`heuristics.py`), baseline and Expectimax search agents (`agents.py`, `expectimax.py`), Pygame GUI (`gui.py`), CLI (`main.py`), seeded multiprocessing benchmarking and chart pipeline (`experiments.py`), and project documentation.

---

## Repository Structure

```text
2048-Expectimax-AI/
├── README.md                 # Project overview, setup, usage, and benchmark summary
├── requirements.txt          # Pinned external Python dependencies
├── .gitignore                # Excludes caches, virtual environments, and local artifacts
├── docs/                     # Project proposal and final report (Markdown + PDF)
├── src/
│   ├── board.py              # 4x4 2048 game environment, move mechanics, and tile spawning
│   ├── heuristics.py         # 4-component log2 heuristic evaluator (corner, empty, mono, smooth)
│   ├── agents.py             # Base Agent class, RandomAgent, and GreedyAgent (Depth-1)
│   ├── expectimax.py         # ExpectimaxAgent (MAX/CHANCE tree search, Depth 1–3)
│   ├── experiments.py        # Headless multi-core benchmarking, CSV export, and chart generation
│   ├── gui.py                # Interactive Pygame desktop interface with live telemetry
│   ├── main.py               # Interactive console menu (Human play, AI watch, benchmarks)
│   └── cli_utils.py          # Shared terminal input/display utilities
└── outputs/
    ├── results/              # per_game_results.csv and summary_table.csv
    └── figures/              # Generated Matplotlib comparison charts (bar, box, line)
```

---

## Setup Instructions

**Prerequisites:** Python 3.10 or higher.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mdaniyalalam/2048-Expectimax-AI.git
   cd 2048-Expectimax-AI
   ```

2. **(Optional) Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS / Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Run

### Launch the Graphical Interface (Recommended)
```bash
python src/gui.py
```
* Switch live between **Human**, **Random**, **Greedy (D1)**, and **Expectimax (D1–D3)** modes.
* Adjust search depth, playback speed (`Slow` / `Normal` / `Fast`), and heuristic weights (`w_corner`, `w_empty`, `w_mono`, `w_smooth`) in real time while inspecting live node counts and heuristic scores.
* **Keyboard shortcuts:** Arrow keys / `WASD` (Human mode), `Space` (Play/Pause AI), `R` (Reset).

### Launch the Interactive Console Menu
```bash
python src/main.py
```
* Provides terminal-based Human play, live AI watch modes, and an interactive benchmark runner.

---

## Reproducing the Benchmark Results

All experimental tables (`outputs/results/`) and charts (`outputs/figures/`) in the Final Report are generated from a single deterministic, fixed-seed command (`base_seed=42`, 50 games per agent):

```bash
python src/experiments.py --games 50 --seed 42
```

**Optional CLI flags:**
* `--workers N` — Set the number of parallel worker processes (defaults to `CPU cores - 1`). Example: `python src/experiments.py --games 50 --seed 42 --workers 10`
* `--no-depth3` — Skip Expectimax Depth-3 for a quick verification run (~1–2 minutes).
* `--no-charts` — Export CSV tables only without regenerating PNG figures.

*Data Note:* No external dataset is used; all game instances are generated procedurally from the fixed base seed (`42` through `91`), ensuring identical starting boards and tile-spawn sequences across all agents.

---

## Benchmark Summary (50 Seeded Games, Base Seed = 42)

| Agent | Avg Score | Std Dev | Median Score | Best Tile | % ≥ 1024 | % ≥ 2048 | Avg Nodes / Move | Avg CPU Time / Game |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Random** | 1,105 | 603 | 1,070 | 256 | 0.0% | 0.0% | 1.0 | 0.01s |
| **Greedy (D1)** | 11,237 | 6,774 | 10,668 | 2048 | 52.0% | 10.0% | 3.6 | 0.06s |
| **Expectimax (D2)** | 32,736 | 16,386 | 32,452 | 4096 | 94.0% | 74.0% | 200.9 | 5.23s |
| **Expectimax (D3)** | 44,262 | 17,096 | 37,566 | 4096 | 100.0% | 90.0% | 6,405.5 | 224.97s |

*Expectimax (D3) achieved a 35.2% higher average score than Depth-2 and reached the 4096 tile in 38% of games (vs. 18% for D2), at the cost of 31.9× more nodes expanded per move and 43.0× more CPU time per game.*

---

## Features

* **Pure-Python Expectimax Engine:** Implements full MAX and CHANCE node recursion with exact `0.9` / `0.1` spawn probabilities (`2` vs. `4`), terminal game-over penalty (`-1000.0`), and configurable depth limits (D1–D3).
* **Optimized Four-Component Heuristic:** Evaluates board states using `log2`-scaled Corner, Empty Cell, Monotonicity, and Smoothness metrics with an O(1) lookup table.
* **Interactive Pygame Visualizer:** Real-time board rendering, step-by-step execution, live weight tuning, and per-move node/utility telemetry.
* **Reproducible Multi-Core Benchmarking:** Deterministic per-game RNG seeding, parallel execution via `ProcessPoolExecutor`, live progress/ETA display, and automatic CSV + Matplotlib chart generation.

---

## Known Limitations

* **Exponential Branching at Depth 3+:** Even with a chance-node branch cap of 6 empty cells per layer at Depth-3, pure-Python search averages ~6,405 nodes/move (~225s CPU time per game), making Depth-4+ impractical without transposition tables, bitboard representation, or a compiled backend (C/C++/Cython).
* **Sampling Variance in Early Depth-3 States:** When more than 6 empty cells are open, Depth-3 randomly samples 6 cells at each chance node rather than enumerating all empty squares; once the board tightens to ≤6 empty cells, search is 100% exact.
* **Static Heuristic Weights:** The four heuristic weights (`w_corner=1.0`, `w_empty=2.0`, `w_mono=1.0`, `w_smooth=0.5`) remain fixed throughout the game rather than adapting dynamically between early-game and late-game (2048+/4096+) board states.
