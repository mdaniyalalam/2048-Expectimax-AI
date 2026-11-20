"""Heuristic evaluation function for scoring 2048 board states."""

_LOG2 = {0: 0.0, **{1 << p: float(p) for p in range(1, 20)}}

class HeuristicEvaluator:
    """The utility is a weighted sum of four heuristics:

      corner      biggest tile sits in a corner
      empty       number of empty cells
      mono        rows/columns that only go up or down
      smooth      neighbouring tiles have similar values

    Tile values are converted with log2 (2->1, 4->2, 8->3 ...) so that a huge tile
    does not drown out everything else."""

    def __init__(self, w_corner=1.0, w_empty=2.0, w_mono=1.0, w_smooth=0.5):
        self.w_corner = w_corner
        self.w_empty = w_empty
        self.w_mono = w_mono
        self.w_smooth = w_smooth

    def components(self, board):
        """The four raw heuristic values (before weighting), as a dict."""
        g = board.grid
        log = _LOG2
        r0, r1, r2, r3 = g[0], g[1], g[2], g[3]
        a0, a1, a2, a3 = log[r0[0]], log[r0[1]], log[r0[2]], log[r0[3]]
        b0, b1, b2, b3 = log[r1[0]], log[r1[1]], log[r1[2]], log[r1[3]]
        c0, c1, c2, c3 = log[r2[0]], log[r2[1]], log[r2[2]], log[r2[3]]
        d0, d1, d2, d3 = log[r3[0]], log[r3[1]], log[r3[2]], log[r3[3]]

        empty = (
            (a0 == 0) + (a1 == 0) + (a2 == 0) + (a3 == 0)
            + (b0 == 0) + (b1 == 0) + (b2 == 0) + (b3 == 0)
            + (c0 == 0) + (c1 == 0) + (c2 == 0) + (c3 == 0)
            + (d0 == 0) + (d1 == 0) + (d2 == 0) + (d3 == 0)
        )
        top = max(a0, a1, a2, a3, b0, b1, b2, b3, c0, c1, c2, c3, d0, d1, d2, d3)
        corner = top if (top == a0 or top == a3 or top == d0 or top == d3) else 0.0

        mono = 0.0
        smooth = 0.0
        for x0, x1, x2, x3 in (
            (a0, a1, a2, a3), (b0, b1, b2, b3), (c0, c1, c2, c3), (d0, d1, d2, d3),
            (a0, b0, c0, d0), (a1, b1, c1, d1), (a2, b2, c2, d2), (a3, b3, c3, d3),
        ):
            up = down = 0.0
            diff = x1 - x0
            if diff > 0:
                up += diff
            else:
                down -= diff
            if x0 and x1:
                smooth += abs(diff)

            diff = x2 - x1
            if diff > 0:
                up += diff
            else:
                down -= diff
            if x1 and x2:
                smooth += abs(diff)

            diff = x3 - x2
            if diff > 0:
                up += diff
            else:
                down -= diff
            if x2 and x3:
                smooth += abs(diff)

            mono += up if up < down else down

        return {"corner": corner, "empty": float(empty), "mono": -mono, "smooth": -smooth}

    def evaluate(self, board):
        """The utility of a board: weighted sum of the four heuristics."""
        c = self.components(board)
        return (
            self.w_corner * c["corner"] + self.w_empty * c["empty"]
            + self.w_mono * c["mono"] + self.w_smooth * c["smooth"]
        )
