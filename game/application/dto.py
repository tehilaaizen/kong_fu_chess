from __future__ import annotations

from engine.game_snapshot import GameSnapshot
from model.position import Position


def board_placements(snapshot: GameSnapshot) -> list[dict]:
    """Serialize a GameSnapshot's pieces as a list of plain
    {id, color, kind, row, col} records - the serializable board shape the
    server sends in a state_snapshot. Unlike a bare token grid, this keeps
    each piece's stable id, so a client can key its per-piece animator off
    the same id the motion/arrival events carry. Lives in the application
    layer (which may see engine DTOs) so server/ never imports the engine
    just to describe a board."""
    return [
        {"id": placement.id, "color": placement.color, "kind": placement.kind,
         "row": placement.cell.row, "col": placement.cell.col}
        for placement in snapshot.pieces
    ]


def cell(position: Position) -> dict:
    """Serialize one board cell as a plain {row, col} record for the wire."""
    return {"row": position.row, "col": position.col}
