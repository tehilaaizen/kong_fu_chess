import pytest

from errors import EMPTY_BOARD, ROW_WIDTH_MISMATCH, UNKNOWN_TOKEN, BoardValidationError
from model.position import Position
from text_io.board_parser import BoardParser


def test_parses_a_rectangular_board():
    board = BoardParser.parse("wK . .\n. wR .\n. . bN\n. . bK")

    assert board.width == 3
    assert board.height == 4
    assert board.piece_at(Position(0, 0)).color == "w"
    assert board.piece_at(Position(0, 0)).kind == "K"
    assert board.piece_at(Position(3, 2)).color == "b"
    assert board.piece_at(Position(3, 2)).kind == "K"


def test_empty_cells_hold_no_piece():
    board = BoardParser.parse("wK . .\n. . .")

    assert board.is_empty(Position(0, 1))
    assert board.is_empty(Position(1, 2))


def test_assigns_a_distinct_id_to_each_piece():
    board = BoardParser.parse("wK . bK")

    king = board.piece_at(Position(0, 0))
    rook = board.piece_at(Position(0, 2))

    assert king.id != rook.id


def test_rejects_empty_text():
    with pytest.raises(BoardValidationError) as excinfo:
        BoardParser.parse("")

    assert excinfo.value.code == EMPTY_BOARD


def test_rejects_inconsistent_row_length():
    with pytest.raises(BoardValidationError) as excinfo:
        BoardParser.parse("wK . .\n. wR")

    assert excinfo.value.code == ROW_WIDTH_MISMATCH


def test_rejects_unknown_token():
    with pytest.raises(BoardValidationError) as excinfo:
        BoardParser.parse("wK . Z")

    assert excinfo.value.code == UNKNOWN_TOKEN
