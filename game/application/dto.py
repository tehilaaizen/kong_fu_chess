from __future__ import annotations

from engine.game_snapshot import GameSnapshot

EMPTY_CELL = "."


def board_grid(snapshot: GameSnapshot) -> list[list[str]]:
    """Turn a GameSnapshot into a plain height x width grid of tokens
    ("wR"/"bK"/... or "." for an empty cell) - the serializable board
    shape the server sends in a state_snapshot. Lives in the application
    layer (which may see engine DTOs) so server/ never imports the engine
    just to describe a board."""
    grid = [[EMPTY_CELL] * snapshot.board_width for _ in range(snapshot.board_height)]
    for placement in snapshot.pieces:
        grid[placement.cell.row][placement.cell.col] = placement.color + placement.kind
    return grid
