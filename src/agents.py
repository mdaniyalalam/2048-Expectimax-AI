"""Base agent interface and baseline players (Random and Greedy)."""

import math
import random

from heuristics import HeuristicEvaluator


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
