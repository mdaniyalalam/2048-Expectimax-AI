"""2048 game environment and board state mechanics."""

import random

SIZE = 4
DIRECTIONS = ["left", "right", "up", "down"]
KEYS = {"a": "left", "d": "right", "w": "up", "s": "down"}

def _flip(grid):
    return [row[::-1] for row in grid]

def _transpose(grid):
    return [list(col) for col in zip(*grid)]

# Each direction maps to (forward, back) transforms that reduce it to a left slide.
_TRANSFORMS = {
    "left": (lambda g: g, lambda g: g),
    "right": (_flip, _flip),
    "up": (_transpose, _transpose),
    "down": (lambda g: _flip(_transpose(g)), lambda g: _transpose(_flip(g))),
}

class Board:
    """A 4x4 2048 board. 0 means an empty cell."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.grid = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self.add_tile()
        self.add_tile()

    def copy(self):
        """Independent copy, used by agents to try moves safely."""
        other = Board.__new__(Board)
        other.rng, other.score = self.rng, self.score
        other.grid = [row[:] for row in self.grid]
        return other

    def empty_cells(self):
        """List of (row, col) positions that are empty."""
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if self.grid[r][c] == 0]

    def add_tile(self):
        """Place a 2 (90%) or a 4 (10%) on a random empty cell."""
        cells = self.empty_cells()
        if cells:
            r, c = self.rng.choice(cells)
            self.grid[r][c] = 2 if self.rng.random() < 0.9 else 4

    @staticmethod
    def _slide_row_left(row):
        """Slide one row left and merge equal neighbours. Returns (new_row, points_gained)."""
        tiles = [v for v in row if v]
        merged, gained, i = [], 0, 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                merged.append(tiles[i] * 2)
                gained += tiles[i] * 2
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        return merged + [0] * (SIZE - len(merged)), gained

    def slide(self, direction):
        """Slide the board without spawning a tile. Returns True if anything moved."""
        if direction not in _TRANSFORMS:
            raise ValueError(f"Unknown direction: {direction}")
        forward, back = _TRANSFORMS[direction]
        results = [self._slide_row_left(line) for line in forward(self.grid)]
        new_grid = back([line for line, _ in results])
        self.score += sum(gained for _, gained in results)
        moved = new_grid != self.grid
        self.grid = new_grid
        return moved

    def step(self, direction):
        """Play a real turn: slide, then spawn a tile if anything moved."""
        moved = self.slide(direction)
        if moved:
            self.add_tile()
        return moved

    def legal_moves(self):
        """Directions that would change the board."""
        return [d for d in DIRECTIONS if self.copy().slide(d)]

    def is_game_over(self):
        """True when there is no empty cell and no merge is possible."""
        if self.empty_cells():
            return False
        g = self.grid
        return not any(
            g[i][j] == g[i][j + 1] or g[j][i] == g[j + 1][i]
            for i in range(SIZE) for j in range(SIZE - 1)
        )

    def max_tile(self):
        """Value of the biggest tile on the board."""
        return max(map(max, self.grid))

    move = step
    get_valid_moves = legal_moves
    spawn_tile = add_tile

    def __str__(self):
        return "\n".join(" ".join(f"{v:5d}" if v else "    ." for v in row) for row in self.grid)

Board2048 = Board
