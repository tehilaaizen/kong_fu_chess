import pytest

from model.position import Position
from text_io.move_notation import InvalidMoveNotation, MoveNotation

BOARD_HEIGHT = 8


def test_parses_color_kind_and_both_cells():
    parsed = MoveNotation.parse("WQe2e5", BOARD_HEIGHT)

    assert parsed.color == "w"
    assert parsed.kind == "Q"
    assert parsed.source == Position(6, 4)  # e2: col 4, row 8-2
    assert parsed.destination == Position(3, 4)  # e5: col 4, row 8-5


def test_rank_one_is_the_bottom_row_and_rank_eight_the_top():
    parsed = MoveNotation.parse("WRa1h8", BOARD_HEIGHT)

    assert parsed.source == Position(7, 0)  # a1: col 0, bottom row
    assert parsed.destination == Position(0, 7)  # h8: col 7, top row


def test_black_pawn_move():
    parsed = MoveNotation.parse("bPa7a5", BOARD_HEIGHT)

    assert parsed.color == "b"
    assert parsed.kind == "P"
    assert parsed.source == Position(1, 0)  # a7
    assert parsed.destination == Position(3, 0)  # a5


def test_color_and_kind_are_case_insensitive():
    parsed = MoveNotation.parse("wqe2e5", BOARD_HEIGHT)

    assert parsed.color == "w"
    assert parsed.kind == "Q"


@pytest.mark.parametrize("bad", ["WQe2e", "WQe2e55", "", "WQe2"])
def test_wrong_length_is_rejected(bad):
    with pytest.raises(InvalidMoveNotation):
        MoveNotation.parse(bad, BOARD_HEIGHT)


def test_unknown_color_is_rejected():
    with pytest.raises(InvalidMoveNotation):
        MoveNotation.parse("XQe2e5", BOARD_HEIGHT)


def test_unknown_kind_is_rejected():
    with pytest.raises(InvalidMoveNotation):
        MoveNotation.parse("WXe2e5", BOARD_HEIGHT)


def test_non_algebraic_cell_is_rejected():
    with pytest.raises(InvalidMoveNotation):
        MoveNotation.parse("WQe2e#", BOARD_HEIGHT)


def test_non_digit_rank_is_rejected():
    with pytest.raises(InvalidMoveNotation):
        MoveNotation.parse("WQeaee", BOARD_HEIGHT)
