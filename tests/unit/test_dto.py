from application.dto import EMPTY_CELL, board_grid
from engine.game_snapshot import GameSnapshot, PiecePlacement
from model.position import Position


def test_board_grid_places_each_piece_and_leaves_the_rest_empty():
    snapshot = GameSnapshot(
        board_width=3,
        board_height=2,
        pieces=[
            PiecePlacement(id=1, kind="R", color="w", cell=Position(1, 0)),
            PiecePlacement(id=2, kind="K", color="b", cell=Position(0, 2)),
        ],
    )

    grid = board_grid(snapshot)

    assert grid == [
        [EMPTY_CELL, EMPTY_CELL, "bK"],
        ["wR", EMPTY_CELL, EMPTY_CELL],
    ]


def test_an_empty_board_is_all_empty_cells():
    snapshot = GameSnapshot(board_width=2, board_height=2, pieces=[])

    assert board_grid(snapshot) == [[EMPTY_CELL, EMPTY_CELL], [EMPTY_CELL, EMPTY_CELL]]
