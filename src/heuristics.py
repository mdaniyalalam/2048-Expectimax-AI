"""Heuristic evaluation function for scoring 2048 board states."""

import math

from board import SIZE


class HeuristicEvaluator:
    """Scores a board from 'how good does this look for the player?'.
    Higher = better. The utility is a weighted sum of four heuristics:

      corner      biggest tile sits in a corner
      empty       number of empty cells
      monotonic   rows/columns that only go up or down
      smooth      neighbouring tiles have similar values

    Tile values are converted with log2 (2->1, 4->2, 8->3 ...) so that a huge tile
    does not drown out everything else."""

    def __init__(self, w_corner=1.0, w_empty=2.0, w_mono=1.0, w_smooth=0.5):
        self.w_corner = w_corner
        self.w_empty = w_empty
        self.w_mono = w_mono
        self.w_smooth = w_smooth

    @staticmethod
    def _log(value):
        """log2 of a tile value; empty cells count as 0."""
        return math.log2(value) if value > 0 else 0.0

    def corner_score(self, board):
        """log2(max tile) if a biggest tile is in a corner, otherwise 0."""
        g, last = board.grid, SIZE - 1
        corners = (g[0][0], g[0][last], g[last][0], g[last][last])
        biggest = board.max_tile()
        return self._log(biggest) if biggest in corners else 0.0

    def empty_score(self, board):
        """Number of empty cells (0 to 16)."""
        return float(len(board.empty_cells()))

    def monotonicity_score(self, board):
        """Minus the total amount by which rows and columns break a steady
        increase or decrease. 0 means all 8 lines are perfectly monotonic."""
        g = board.grid
        lines = [row for row in g] + [list(col) for col in zip(*g)]
        penalty = 0.0
        for line in lines:
            vals = [self._log(v) for v in line]
            up = down = 0.0
            for a, b in zip(vals, vals[1:]):
                if a > b:
                    down += a - b        # line is going down here
                else:
                    up += b - a          # line is going up here
            penalty += min(up, down)     # cost of the less-followed direction
        return -penalty

    def smoothness_score(self, board):
        """Minus the sum of log-differences between touching non-empty tiles."""
        g = board.grid
        total = 0.0
        for r in range(SIZE):
            for c in range(SIZE):
                if g[r][c] == 0:
                    continue
                here = self._log(g[r][c])
                if c + 1 < SIZE and g[r][c + 1] != 0:
                    total += abs(here - self._log(g[r][c + 1]))
                if r + 1 < SIZE and g[r + 1][c] != 0:
                    total += abs(here - self._log(g[r + 1][c]))
        return -total

    def components(self, board):
        """The four raw heuristic values (before weighting), as a dict."""
        return {
            "corner": self.corner_score(board),
            "empty": self.empty_score(board),
            "mono": self.monotonicity_score(board),
            "smooth": self.smoothness_score(board),
        }

    def evaluate(self, board):
        """The utility of a board: weighted sum of the four heuristics."""
        c = self.components(board)
        return (
            self.w_corner * c["corner"]
            + self.w_empty * c["empty"]
            + self.w_mono * c["mono"]
            + self.w_smooth * c["smooth"]
        )
