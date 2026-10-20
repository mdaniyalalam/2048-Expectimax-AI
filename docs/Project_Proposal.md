

| ![FAST NUCES logo][image1] | FAST — NATIONAL UNIVERSITY OF COMPUTER AND EMERGING SCIENCES FAST School of Computing  ·  Karachi Campus  ·  Department of Artificial Intelligence & Data Science *AL-2002  Artificial Intelligence (Laboratory)  ·  Fall 2026* |
| :---- | :---: |

**PROJECT PROPOSAL**

*Semester Lab Project  ·  Weightage 1 mark*

## **Group Information**

|  | Name | Roll Number | Section | Role in the project |
| :---- | :---- | :---- | :---- | :---- |
| **Leader** | Muhammad Daniyal Alam | 24K-2048 | BCY-5A | Sole Developer: Full implementation of the project |

| Project Title | 2048 AI with Expectimax  |
| :---- | :---- |
| **Project Idea** | Idea No. 6  from the Project Ideas list |
| **Category** | Part A — Game ☑           Part B — Applied / Data ☐ |
| **GitHub Repository URL** | https\://github.com/mdaniyalalam/2048-Expectimax-AI |
| **Date of Submission** | October 20, 2026  |

# **1\.  Project Title and Summary**

| Title: 2048 AI with Expectimax  Summary: This project is a fully playable version of the popular sliding tile puzzle game 2048, featuring both a manual player mode and an automated artificial intelligence solver. It is designed for puzzle enthusiasts who want to play the classic game, as well as students and developers interested in observing how an AI tackles decision-making under uncertainty. In 2048, new tiles spawn randomly in empty spaces after every move, making it impossible to plan a guaranteed sequence of steps in advance. To overcome this, the software uses an Expectimax search algorithm that "thinks ahead" by calculating the mathematical average of all possible random tile spawns before deciding on the best move. The AI's foresight is guided by custom evaluation rules that score the board based on human-like strategies, such as keeping the largest tiles tucked safely in a corner and maximizing empty space. Ultimately, this allows the AI to navigate the game's randomness and consistently reach high-value tiles, achieving scores that a plain, rule-based program could not accomplish.  |
| :---- |

# **2\.  Problem Statement and Motivation**

| The project addresses the challenge of sequential decision-making in highly stochastic environments, specifically modeled through the puzzle game 2048\. 2048 is deceptively difficult to solve by hand or brute force due to its immense search space and inherent uncertainty. After each player move, the environment randomly spawns a '2' or '4' tile in any empty cell. Because the branching factor depends on the number of empty tiles and two possible tile values, a single move can generate up to 30 immediate environmental responses. Looking ahead just three turns expands the search tree to hundreds of thousands of probabilistic states, rendering blind enumeration and standard deterministic search completely useless. AI developers and puzzle enthusiasts face this challenge constantly; humans cope by intuitively applying positional heuristics, such as anchoring the largest tile in a corner, rather than calculating exact probabilities. Solving this problem computationally using Expectimax is worthwhile because it demonstrates how an intelligent agent can optimize long-term utility in unpredictable real-world scenarios where environments act randomly rather than adversarially.  |
| :---- |

# **3\.  Problem Formulation**

## **3.1  PEAS Description**

| Component | Description for your project |
| :---- | :---- |
| **Performance measure** | The primary metric is the highest tile reached on the board (e.g., 2048, 4096\) before a game-over state. Secondary measures include the cumulative game score (gained by merging tiles) and the total number of moves survived  |
| **Environment** | A $4\times 4$ spatial grid where cells are either empty or contain a tile with a value that is a power of 2 (2, 4, 8, …). After every valid move, the environment randomly spawns a new tile (90% chance of a '2', 10% chance of a '4') in an available empty space  |
| **Actuators** | The agent outputs one of four discrete directional commands: Up, Down, Left, or Right. These commands slide all tiles in the chosen direction and merge adjacent identical tiles.  |
| **Sensors** | The agent perfectly reads the current state of the $4\times 4$ matrix, identifying the exact values and positional coordinates of all tiles and empty spaces before making a decision.  |

## **3.2  Environment and Agent Type**

| Property | Classification — tick one |
| :---- | :---- |
| Observability | Fully observable  ☑           Partially observable  ☐ |
| Determinism | Deterministic  ☐          Stochastic  ☑  |
| Change over time | Static  ☑         Dynamic  ☐ |
| State and actions | Discrete  ☑          Continuous  ☐ |
| Agents | Single-agent  ☑        Multi-agent / adversarial  ☐ |
| Agent type | Simple reflex  ☐    Model-based  ☐    Goal-based  ☐    Utility-based  ☑    Learning  ☐ |

## **3.3  Problem Representation**

| Element | Your representation |
| :---- | :---- |
| **State representation** | A $4\times 4$ integer matrix where each cell contains either empty (0) or a power of 2 representing a tile's current value.  |
| **Actions / moves** | Four discrete directional moves: Up, Down, Left, and Right.  |
| **Initial state** | A $4\times 4$ matrix initialized with mostly empty cells and exactly two randomly placed tiles (each carrying a 90% probability of being a '2' and a 10% probability of being a '4').  |
| **Goal or terminal test** | The terminal test is triggered when the board is in a "Game Over" state, meaning there are zero empty cells left and no adjacent tiles horizontally or vertically share the same value to allow a merge.  |
| **Cost, utility, fitness or evaluation** | A custom utility function evaluated at the leaf nodes of the search tree. It calculates a weighted sum based on four heuristics: anchoring the maximum tile in a corner, maximizing empty cell count, maintaining grid monotonicity, and penalizing adjacent tile variance (smoothness).  |

# **4\.  Proposed AI Approach**

| \# | Technique | Role in the project | Own code or library |
| :---: | :---- | :---- | :---- |
| 1 | Expectimax Search  | Explores a limited-depth game tree alternating between player actions (max nodes) and random tile spawns (chance nodes) to find the optimal move.  | Own code  |
| 2 | Heuristic Evaluation  | Assigns a utility score to future board states based on human-like 2048 strategies, guiding the Expectimax search. | Own code  |
| B | Baseline: Random Play  | Serves as a control variable by picking a random valid direction, measuring how much Expectimax improves performance.  | Own code  |
| B | Baseline: Greedy Search (Depth-1)  | Acts as a secondary baseline that maximizes immediate heuristic score without anticipating future tile spawns. | Own code  |

| Expectimax search is perfectly suited for 2048 because the environment is stochastic rather than strictly adversarial. Instead of assuming an opponent makes the worst move, Expectimax calculates the mathematical average of all possible random tile spawns, optimizing for the highest probable utility. Because the search space expands rapidly, tree depth is limited to 2-3 moves. To assess these future states, my evaluation function scores the board using four adjustable heuristics: anchoring the largest tile in a corner, maximizing empty tiles, promoting monotonicity, and penalizing adjacent tile variance. To rigorously test the system, I will compare Expectimax against two alternatives. A baseline Random Agent will randomly pick valid moves to measure basic competence, while a Greedy Agent (Depth-1 search) will show whether multi-step Expectimax planning actually outperforms short-term heuristic maximization.  |
| :---- |

## **4.1  Planned Class Design**

| 1\. Board2048 (The Environment):      Attributes:  grid, score      Methods: move(direction), get\_valid\_moves(), spawn\_tile(), is\_game\_over(), copy()     Relationship: An independent class representing the game state. It is passed as an argument to the agents so they can simulate future moves.  |
| :---- |
| **2\. BaseAgent (Abstract Parent Class):    Attributes:** None required strictly for logic    **Methods:** select\_move(board)     **Relationship:** The base class establishing polymorphism for the game loop, ensuring any agent can be swapped in seamlessly. **3\. RandomAgent (Subclass):    Attributes:** Inherits from BaseAgent     **Methods:** select\_move(board)     **Relationship:** Child of BaseAgent; serves as the primary experimental baseline.  **4\. ExpectimaxAgent (Subclass):    Attributes:** depth, nodes\_expanded, w\_corner, w\_empty, w\_mono, w\_smooth     **Methods:** select\_move(board), expectimax(board, depth, is\_player\_turn), evaluate(board)     **Relationship:** Child of BaseAgent. It houses the core artificial intelligence logic for the project.  |

# **5\.  Scope**

**In scope:**

| \# | Feature | Why it is essential |
| :---: | :---- | :---- |
| 1 | Playable 2048 Game Engine  | Provides the foundational environment, grid logic, and Pygame graphical interface required for both human play and AI integration.  |
| 2 | Expectimax Search Agent  | The core algorithmic requirement for this project, necessary to navigate the game's stochastic tile-spawning mechanics at a search depth of 2 to 3\.  |
| 3 | Adjustable Heuristic Evaluation  | Essential for scoring the leaf nodes of the Expectimax tree; relies on four weighted rules (corner anchoring, empty tiles, smoothness, monotonicity) to guide decision-making.  |
| 4 | Auto-Play Toggle Mode  | Allows the Expectimax agent to execute moves automatically without human intervention, which is necessary for running high-speed simulations.  |
| 5 | 50-Game Benchmark Evaluation  | Required to statistically prove the Expectimax agent's superiority by comparing its highest tile reached and average score against a Random/Greedy baseline.  |

**Out of scope:**

| The Expectimax search depth is strictly capped at 3; depths of 4 or higher are out of scope because the massive branching factor slows down real-time move calculation to an unplayable degree. Deployment to web or mobile platforms is excluded; the project will run entirely as a local desktop application using Python and Pygame.  |
| :---- |

# **6\.  Data or Environment Source**

| Source name and URL | Self-contained Python Environment  |
| :---- | :---- |
| **Type** | Public dataset  ☐     Web API  ☐     Self-collected  ☐     Generated / simulated  ☑ |
| **Access requirements** | No key needed  ☑    Free key required  ☐     (Paid sources are not permitted) |
| **Approximate size** | Negligible (in-memory $4\times 4$ integer matrices).  |
| **Licence / terms of use** | N/A (Original student code)  |
| **Offline fallback** | The game runs 100% offline without network requests.  |

# **7\.  Evaluation Plan**

| What will be compared | The Expectimax Agent (at search depths 2 and 3\) will be compared against a Greedy Agent (Depth 1\) and a Random Agent.  |
| :---- | :---- |
| **Metric(s)** | Highest tile reached, average total game score, and average nodes expanded per move.  |
| **Baseline** | Random Agent (selects random valid moves) and Greedy Agent (selects the best immediate move without evaluating chance nodes).  |
| **Test instances / test set** | Full 2048 game simulations running from the initial empty state until a terminal "Game Over" state is reached.  |
| **Number of runs and seed** | 50 complete game runs per agent configuration, utilizing a fixed seed (random.seed(42)) to ensure exact reproducibility of the tile spawns.  |
| **Planned charts (at least three)** | Bar chart, Box plot, Line chart   |

# **8\.  Division of Work**

| Member | Modules / components owned | Approximate share |
| :---- | :---- | :---: |
| Muhammad Daniyal Alam  | Full project lifecycle  | 100% (Solo Project)  |

# **9\.  Milestones and Timeline**

| \# | Milestone — what will be demonstrably working | Target date | Owner |
| :---: | :---- | :---- | :---- |
| 1 | Playable 2048 game engine in Pygame with manual arrow-key controls, accurate tile merging, and randomized tile spawning. | Oct 28, 2026  | Muhammad Daniyal Alam  |
| 2 | Random and Depth-1 Greedy agents successfully complete auto-play games; evaluation function calculates board utility using the 4 core heuristics.  | Nov 04, 2026  | Muhammad Daniyal Alam  |
| 3 | Expectimax agent successfully plays the game at Depth 2 and Depth 3\. | Nov 11, 2026  | Muhammad Daniyal Alam  |
| 4 | Headless experiment script successfully runs 50 seeded games for all three agents and generates the 3 required comparative Matplotlib charts.  | Nov 18, 2026  | Muhammad Daniyal Alam  |
| 5 | Experiments complete, final integration, documentation and repository cleanup. | Nov 23, 2026  | Muhammad Daniyal Alam  |

# **10\.  Expected Outcome and Risks**

| A working submission will feature a Pygame interface where users can manually play 2048 or toggle an auto-play mode to watch the Expectimax agent solve the board. I expect the final evaluation to show Expectimax consistently reaching the 1024 or 2048 tile, vastly outperforming the Random and Greedy baselines in average score. The primary risk is the massive branching factor making Depth 3 search too slow for real-time play. If this occurs, I will cap chance node evaluations to only the top empty cells or restrict the depth to 2\. A secondary risk is heuristic weight conflicts causing board lock-ups. I will mitigate this by running headless batch simulations to systematically tune the weights for optimal performance. |
| :---- |

| For office use — Lab Instructor |  |
| :---- | :---- |
| Proposal status | Approved  ☐          Approved with changes  ☐          Revision required  ☐ |
| Comments |  |
| Signature and date |  |

*End of Project Proposal*

[image1]: <data:image/png;base64,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> "FAST logo"