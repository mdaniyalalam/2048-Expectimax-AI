"""Expectimax search agent for 2048."""

from agents import Agent
from board import DIRECTIONS
from heuristics import HeuristicEvaluator

def _weight_property(name):
    """Expose an evaluator weight as an attribute of the agent."""
    return property(
        lambda self: getattr(self.evaluator, name),
        lambda self, value: setattr(self.evaluator, name, value),
    )

class ExpectimaxAgent(Agent):
    """Expectimax search agent for 2048.

    Alternates between:
      - MAX nodes (is_player_turn=True): the player picks a slide that maximizes
        expected heuristic utility.
      - CHANCE nodes (is_player_turn=False): the environment spawns a 2 (p=0.9) or
        a 4 (p=0.1) uniformly over the empty cells.

    'depth' counts full player turns:
      - depth 1: evaluate the board right after the player's first slide.
      - depth 2: slide, spawn, response slide, evaluate.
      - depth 3: three slides interleaved with two spawn layers.

    At depth 3 and above, chance nodes sample at most 'max_chance_branches'
    (default 6) empty cells to keep search time reasonable.
    """

    PROB_2 = 0.9
    PROB_4 = 0.1
    w_corner = _weight_property("w_corner")
    w_empty = _weight_property("w_empty")
    w_mono = _weight_property("w_mono")
    w_smooth = _weight_property("w_smooth")

    def __init__(self, seed=None, depth=2, evaluator=None, max_chance_branches=None, **weights):
        """'weights' (w_corner, w_empty, w_mono, w_smooth) build a new evaluator unless
        'evaluator' is given, in which case it is shared and the weights are ignored."""
        super().__init__(seed)
        if depth < 1:
            raise ValueError("Expectimax depth must be at least 1.")
        self.depth = depth
        self.evaluator = evaluator or HeuristicEvaluator(**weights)
        self._branch_cap = max_chance_branches

    @property
    def name(self):
        return f"Expectimax (depth-{self.depth})"

    @property
    def max_chance_branches(self):
        """Cap on empty cells sampled per chance node (None means no cap)."""
        if self._branch_cap is not None:
            return self._branch_cap
        return 6 if self.depth >= 3 else None

    def evaluate(self, board):
        """Heuristic utility of a leaf board."""
        return self.evaluator.evaluate(board)

    @staticmethod
    def _slides(board):
        """Yield (direction, board) for each slide that changes the board."""
        for direction in DIRECTIONS:
            child = board.copy()
            if child.slide(direction):
                yield direction, child

    def _after_slide(self, board, depth):
        """Utility of a board just after a player slide, with 'depth' player turns
        left to plan (that slide included)."""
        if depth == 1:
            self.nodes_expanded += 1
            return self.evaluate(board)
        return self.expectimax(board, depth - 1, is_player_turn=False)

    def expectimax(self, board, depth, is_player_turn):
        """Recursive Expectimax search.

        Parameters:
            board (Board): simulated board state (modified in place at chance nodes
                but restored before returning).
            depth (int): remaining player turns to search.
            is_player_turn (bool): True for a MAX node, False for a CHANCE node.

        Returns:
            float: expected heuristic utility of the state.
        """
        self.nodes_expanded += 1
        if depth == 0:
            return self.evaluate(board)

        if is_player_turn:
            scores = [self._after_slide(child, depth) for _, child in self._slides(board)]
            return max(scores) if scores else -1000.0

        empty = board.empty_cells()
        if not empty:
            return self.expectimax(board, depth, is_player_turn=True)

        cap = self.max_chance_branches
        if cap is not None and len(empty) > cap:
            empty = self.rng.sample(empty, cap)

        cell_prob = 1.0 / len(empty)
        total = 0.0
        for r, c in empty:
            # Spawn in place and restore afterwards to avoid copying the board per branch.
            board.grid[r][c] = 2
            u2 = self.expectimax(board, depth, is_player_turn=True)
            board.grid[r][c] = 4
            u4 = self.expectimax(board, depth, is_player_turn=True)
            board.grid[r][c] = 0
            total += cell_prob * (self.PROB_2 * u2 + self.PROB_4 * u4)
        return total

    def _pick(self, board):
        scored = [(self._after_slide(child, self.depth), d) for d, child in self._slides(board)]
        return self._best_of(scored)
