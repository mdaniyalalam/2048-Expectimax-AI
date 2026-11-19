"""Expectimax search agent for 2048."""

import math

from agents import Agent
from board import DIRECTIONS
from heuristics import HeuristicEvaluator


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
      - depth = 3: 3 player slides interleaved with 2 chance spawn layers.
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
