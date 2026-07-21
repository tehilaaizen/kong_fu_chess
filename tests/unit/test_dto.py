from application.dto import board_placements, cell
from engine.game_snapshot import GameSnapshot, PiecePlacement
from model.position import Position


def test_board_placements_serializes_each_piece_with_its_id_and_cell():
    snapshot = GameSnapshot(
        board_width=3,
        board_height=2,
        pieces=[
            PiecePlacement(id=1, kind="R", color="w", cell=Position(1, 0)),
            PiecePlacement(id=2, kind="K", color="b", cell=Position(0, 2)),
        ],
    )

    placements = board_placements(snapshot)

    assert placements == [
        {"id": 1, "color": "w", "kind": "R", "row": 1, "col": 0},
        {"id": 2, "color": "b", "kind": "K", "row": 0, "col": 2},
    ]


def test_an_empty_board_serializes_to_no_placements():
    snapshot = GameSnapshot(board_width=2, board_height=2, pieces=[])

    assert board_placements(snapshot) == []


def test_cell_serializes_a_position_to_row_and_col():
    assert cell(Position(3, 5)) == {"row": 3, "col": 5}
