# Tetris

A minimal, dependency-free Tetris built with Python's standard-library `tkinter`.

## Run

```
python tetris.py
```

Requires Python 3.8+ (tested on 3.12). No `pip install` needed — `tkinter` ships with the standard Python installer.

## Controls

| Key | Action |
| --- | --- |
| ← / → | Move |
| ↓ | Soft drop |
| ↑ or X | Rotate clockwise |
| Z | Rotate counter-clockwise |
| Space | Hard drop |
| P | Pause |
| R | Restart (after game over) |

## Features

- 7-bag randomizer
- Wall kicks on rotation
- Ghost piece
- Soft / hard drop scoring
- Line-clear scoring (100 / 300 / 500 / 800 × level)
- Level-based speed-up every 10 lines
