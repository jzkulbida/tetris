"""A minimal, dependency-free Tetris built on tkinter.

Run:  python tetris.py

Controls:
    Left / Right : move
    Down        : soft drop
    Up  or  X   : rotate clockwise
    Z           : rotate counter-clockwise
    Space       : hard drop
    P           : pause
    R           : restart (after game over)
"""

import random
import tkinter as tk

# ---- Board geometry -------------------------------------------------------
COLS, ROWS = 10, 20
CELL = 30
PAD = 12
SIDEBAR = 6 * CELL

BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL

# ---- Tetromino definitions ---------------------------------------------------
# Each shape is a list of (row, col) offsets for rotation state 0, spawned
# near the top-centre. Rotations are computed by rotating about a pivot.
SHAPES = {
    "I": {"color": "#31c7ef", "cells": [(0, -1), (0, 0), (0, 1), (0, 2)]},
    "O": {"color": "#f7d308", "cells": [(0, 0), (0, 1), (1, 0), (1, 1)]},
    "T": {"color": "#ad4d9c", "cells": [(0, -1), (0, 0), (0, 1), (1, 0)]},
    "S": {"color": "#42b642", "cells": [(0, 0), (0, 1), (1, -1), (1, 0)]},
    "Z": {"color": "#ef2029", "cells": [(0, -1), (0, 0), (1, 0), (1, 1)]},
    "J": {"color": "#5a65ad", "cells": [(0, -1), (0, 0), (0, 1), (1, 1)]},
    "L": {"color": "#ef7921", "cells": [(0, -1), (0, 0), (0, 1), (1, -1)]},
}

GRAVITY_MS = 500          # base fall interval
EMPTY = None


def _shift(hex_color, amount):
    """Lighten (amount > 0) or darken (amount < 0) a #rrggbb color."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = max(0, min(255, r + amount))
    g = max(0, min(255, g + amount))
    b = max(0, min(255, b + amount))
    return f"#{r:02x}{g:02x}{b:02x}"


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.color = SHAPES[kind]["color"]
        self.cells = list(SHAPES[kind]["cells"])
        self.row = 1
        self.col = COLS // 2

    def blocks(self, cells=None, row=None, col=None):
        cells = self.cells if cells is None else cells
        row = self.row if row is None else row
        col = self.col if col is None else col
        return [(row + dr, col + dc) for dr, dc in cells]

    def rotated(self, direction):
        # O never rotates; rotate the rest about (0, 0).
        if self.kind == "O":
            return list(self.cells)
        if direction > 0:
            return [(dc, -dr) for dr, dc in self.cells]
        return [(-dc, dr) for dr, dc in self.cells]


class Tetris:
    def __init__(self, root):
        self.root = root
        root.title("Tetris")
        root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=BOARD_W + SIDEBAR + PAD * 3,
            height=BOARD_H + PAD * 2,
            bg="#101018",
            highlightthickness=0,
        )
        self.canvas.pack()

        for key in ("<Left>", "<Right>", "<Down>", "<Up>",
                    "<space>", "z", "Z", "x", "X", "p", "P", "r", "R"):
            root.bind(key, self.on_key)

        self.reset()
        self.tick()

    # ---- game lifecycle --------------------------------------------------
    def reset(self):
        self.grid = [[EMPTY] * COLS for _ in range(ROWS)]
        self.bag = []
        self.piece = self.spawn()
        self.next_piece = self.spawn()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.over = False
        self.paused = False
        self.drop_delay = GRAVITY_MS

    def refill_bag(self):
        self.bag = list(SHAPES.keys())
        random.shuffle(self.bag)

    def spawn(self):
        if not self.bag:
            self.refill_bag()
        return Piece(self.bag.pop())

    # ---- collision / locking ------------------------------------------------
    def fits(self, blocks):
        for r, c in blocks:
            if c < 0 or c >= COLS or r >= ROWS:
                return False
            if r >= 0 and self.grid[r][c] is not EMPTY:
                return False
        return True

    def lock(self):
        for r, c in self.piece.blocks():
            if r < 0:
                self.over = True
                return
            self.grid[r][c] = self.piece.color
        self.clear_lines()
        self.piece = self.next_piece
        self.next_piece = self.spawn()
        if not self.fits(self.piece.blocks()):
            self.over = True

    def clear_lines(self):
        kept = [row for row in self.grid if any(cell is EMPTY for cell in row)]
        cleared = ROWS - len(kept)
        if cleared:
            self.grid = [[EMPTY] * COLS for _ in range(cleared)] + kept
            self.lines += cleared
            self.score += (0, 100, 300, 500, 800)[cleared] * self.level
            self.level = 1 + self.lines // 10
            self.drop_delay = max(80, GRAVITY_MS - (self.level - 1) * 40)

    # ---- movement -------------------------------------------------------
    def move(self, dr, dc):
        cand = self.piece.blocks(row=self.piece.row + dr, col=self.piece.col + dc)
        if self.fits(cand):
            self.piece.row += dr
            self.piece.col += dc
            return True
        return False

    def rotate(self, direction):
        cells = self.piece.rotated(direction)
        for kick in (0, -1, 1, -2, 2):
            cand = self.piece.blocks(cells=cells, col=self.piece.col + kick)
            if self.fits(cand):
                self.piece.cells = cells
                self.piece.col += kick
                return

    def hard_drop(self):
        dropped = 0
        while self.move(1, 0):
            dropped += 1
        self.score += dropped * 2
        self.lock()
        self.render()

    def step_down(self):
        if not self.move(1, 0):
            self.lock()

    # ---- input ---------------------------------------------------------
    def on_key(self, event):
        k = event.keysym.lower()
        if k == "r" and self.over:
            self.reset()
            self.render()
            return
        if k == "p":
            self.paused = not self.paused
            self.render()
            return
        if self.over or self.paused:
            return

        if k == "left":
            self.move(0, -1)
        elif k == "right":
            self.move(0, 1)
        elif k == "down":
            self.step_down()
        elif k in ("up", "x"):
            self.rotate(1)
        elif k == "z":
            self.rotate(-1)
        elif k == "space":
            self.hard_drop()
        self.render()

    # ---- main loop -------------------------------------------------------
    def tick(self):
        if not self.over and not self.paused:
            self.step_down()
            self.render()
        self.root.after(self.drop_delay, self.tick)

    # ---- rendering -------------------------------------------------------
    def cell_rect(self, r, c, ox=PAD, oy=PAD):
        x = ox + c * CELL
        y = oy + r * CELL
        return x, y, x + CELL, y + CELL

    def draw_cell(self, r, c, color, ox=PAD, oy=PAD):
        if r < 0:
            return
        x1, y1, x2, y2 = self.cell_rect(r, c, ox, oy)
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#101018")
        # top-left bevel highlight
        self.canvas.create_line(x1 + 1, y2 - 1, x1 + 1, y1 + 1, x2 - 1, y1 + 1,
                                fill=_shift(color, 60))
        self.canvas.create_line(x1 + 1, y2 - 1, x2 - 1, y2 - 1, x2 - 1, y1 + 1,
                                fill=_shift(color, -40))

    def render(self):
        cv = self.canvas
        cv.delete("all")

        # playfield frame + grid
        cv.create_rectangle(PAD, PAD, PAD + BOARD_W, PAD + BOARD_H,
                            outline="#3a3a52", width=2)
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] is not EMPTY:
                    self.draw_cell(r, c, self.grid[r][c])

        # ghost piece
        ghost = Piece(self.piece.kind)
        ghost.cells = list(self.piece.cells)
        ghost.row, ghost.col = self.piece.row, self.piece.col
        while self.fits(ghost.blocks(row=ghost.row + 1)):
            ghost.row += 1
        for r, c in ghost.blocks():
            if r >= 0:
                x1, y1, x2, y2 = self.cell_rect(r, c)
                cv.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3,
                                    outline=self.piece.color)

        # active piece
        for r, c in self.piece.blocks():
            self.draw_cell(r, c, self.piece.color)

        # sidebar
        sx = PAD * 2 + BOARD_W
        cv.create_text(sx, PAD, anchor="nw", fill="#e8e8f0",
                       font=("Consolas", 14, "bold"), text="NEXT")
        for dr, dc in SHAPES[self.next_piece.kind]["cells"]:
            self.draw_cell(dr + 2, dc + 1, self.next_piece.color,
                           ox=sx, oy=PAD + 24)

        info = f"SCORE\n{self.score}\n\nLINES\n{self.lines}\n\nLEVEL\n{self.level}"
        cv.create_text(sx, PAD + 5 * CELL, anchor="nw", fill="#e8e8f0",
                       font=("Consolas", 13), text=info)

        if self.paused:
            self.banner("PAUSED", "press P")
        elif self.over:
            self.banner("GAME OVER", "press R")

    def banner(self, title, subtitle):
        cx = PAD + BOARD_W / 2
        cy = PAD + BOARD_H / 2
        self.canvas.create_rectangle(PAD, cy - 46, PAD + BOARD_W, cy + 46,
                                     fill="#000000", outline="")
        self.canvas.create_text(cx, cy - 12, fill="#ffffff",
                                font=("Consolas", 22, "bold"), text=title)
        self.canvas.create_text(cx, cy + 20, fill="#b8b8c8",
                                font=("Consolas", 12), text=subtitle)


def main():
    root = tk.Tk()
    Tetris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
