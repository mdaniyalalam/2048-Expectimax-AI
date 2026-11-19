"""2048 game environment and board state mechanics."""

import random

SIZE = 4
DIRECTIONS = ["left", "right", "up", "down"]
KEYS = {"a": "left", "d": "right", "w": "up", "s": "down"}


class Board:
    """A 4x4 2048 board. 0 means an empty cell."""

    def __init__(self, rng=None):
        # rng = a random number generator. Giving it a seed makes games repeatable.
        self.rng = rng if rng is not None else random.Random()
        self.grid = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self.add_tile()
        self.add_tile()

    def copy(self):
        """Make an independent copy (used by AIs to 'try' a move safely)."""
        other = Board.__new__(Board)
        other.rng = self.rng
        other.grid = [row[:] for row in self.grid]
        other.score = self.score
        return other

    def empty_cells(self):
        """List of (row, col) positions that are empty."""
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if self.grid[r][c] == 0]

    def add_tile(self):
        """Put a 2 (90% of the time) or a 4 (10%) on a random empty cell."""
        cells = self.empty_cells()
        if not cells:
            return
        r, c = self.rng.choice(cells)
        self.grid[r][c] = 2 if self.rng.random() < 0.9 else 4

    @staticmethod
    def _slide_row_left(row):
        """Slide one row to the left and merge equal neighbours.
        Returns (new_row, points_gained)."""
        tiles = [v for v in row if v != 0]       # drop the zeros: [2,0,2,4] -> [2,2,4]
        merged, gained, i = [], 0, 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                merged.append(tiles[i] * 2)      # two equal tiles become one
                gained += tiles[i] * 2
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        merged += [0] * (SIZE - len(merged))     # fill the rest with zeros
        return merged, gained

    def slide(self, direction):
        """Slide the whole board. Does NOT add a new tile.
        Returns True if anything moved, False if the move did nothing."""
        before = [row[:] for row in self.grid]
        g = self.grid
        if direction == "left":
            lines = g
        elif direction == "right":
            lines = [row[::-1] for row in g]
        elif direction == "up":
            lines = [list(col) for col in zip(*g)]
        elif direction == "down":
            lines = [list(col)[::-1] for col in zip(*g)]
        else:
            raise ValueError(f"Unknown direction: {direction}")

        new_lines = []
        for line in lines:
            new_line, gained = self._slide_row_left(line)
            self.score += gained
            new_lines.append(new_line)

        # undo the flipping we did to reuse the "left" logic
        if direction == "left":
            self.grid = new_lines
        elif direction == "right":
            self.grid = [row[::-1] for row in new_lines]
        elif direction == "up":
            self.grid = [list(row) for row in zip(*new_lines)]
        elif direction == "down":
            self.grid = [list(row) for row in zip(*[line[::-1] for line in new_lines])]

        return self.grid != before

    def step(self, direction):
        """A real turn: slide, and if something moved, a new tile appears."""
        moved = self.slide(direction)
        if moved:
            self.add_tile()
        return moved

    def legal_moves(self):
        """Directions that would actually change the board."""
        return [d for d in DIRECTIONS if self.copy().slide(d)]

    def is_game_over(self):
        """True when no direction changes the board (no empty cell and no merge)."""
        return len(self.legal_moves()) == 0

    def max_tile(self):
        """Value of the biggest tile on the board."""
        return max(max(row) for row in self.grid)

    # Proposal Section 4.1 alias methods so both naming conventions work seamlessly
    def move(self, direction):
        """Alias for step(direction) matching Proposal Section 4.1."""
        return self.step(direction)

    def get_valid_moves(self):
        """Alias for legal_moves() matching Proposal Section 4.1."""
        return self.legal_moves()

    def spawn_tile(self):
        """Alias for add_tile() matching Proposal Section 4.1."""
        self.add_tile()

    def __str__(self):
        lines = []
        for row in self.grid:
            lines.append(" ".join(f"{v:5d}" if v else "    ." for v in row))
        return "\n".join(lines)


# Alias Board2048 -> Board to match Proposal Section 4.1 class naming
Board2048 = Board
