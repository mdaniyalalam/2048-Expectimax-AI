"""Base agent interface and baseline players (Random and Greedy)."""

import random
from board import DIRECTIONS
from heuristics import HeuristicEvaluator

class Agent:
    """Base class for all players. Subclasses implement _pick()."""

    name = "Agent"

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.nodes_expanded = 0
        self.total_nodes_expanded = 0
        self.moves_made = 0

    def _pick(self, board):
        """Return a direction (or None if no move is possible), setting self.nodes_expanded."""
        raise NotImplementedError("Subclasses must implement _pick")

    def choose_move(self, board):
        """Return the direction to play on this board, or None if the game is over."""
        self.nodes_expanded = 0
        move = self._pick(board)
        if move is not None:
            self.total_nodes_expanded += self.nodes_expanded
            self.moves_made += 1
        return move

    select_move = choose_move

    def _best_of(self, scored):
        """Pick the highest-scoring move from (score, move) pairs, breaking ties randomly."""
        if not scored:
            return None
        top = max(score for score, _ in scored)
        return self.rng.choice([move for score, move in scored if score == top])

    def avg_nodes_per_move(self):
        """Average search nodes expanded per move over the agent's lifetime."""
        return self.total_nodes_expanded / self.moves_made if self.moves_made else 0.0


BaseAgent = Agent

class RandomAgent(Agent):
    """Baseline: picks any legal move at random."""

    name = "Random"
    
    def _pick(self, board):
        legal = board.legal_moves()
        self.nodes_expanded = 1
        return self.rng.choice(legal) if legal else None

class GreedyAgent(Agent):
    """Depth-1 baseline: picks the move whose resulting board has the best heuristic
    utility. It scores the board right after the slide, before any new tile appears,
    so it never plans for the random spawn."""

    name = "Greedy (depth-1 heuristic)"

    def __init__(self, seed=None, evaluator=None):
        super().__init__(seed)
        self.evaluator = evaluator or HeuristicEvaluator()

    def _pick(self, board):
        scored = []
        for move in DIRECTIONS:
            trial = board.copy()
            if trial.slide(move):
                scored.append((self.evaluator.evaluate(trial), move))
        self.nodes_expanded = len(scored)
        return self._best_of(scored)
