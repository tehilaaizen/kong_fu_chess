import pytest

from model.board import Board, OccupiedCellError
from model.piece import Piece
from model.position import Position


def _king(color="w", cell=Position(0, 0), id=1):
    return Piece(id=id, color=color, kind="K", cell=cell)


def test_dimensions_are_set_at_construction():
    board = Board(width=4, height=6)

    assert board.width == 4
    assert board.height == 6


def test_empty_cell_lookup_returns_none():
    board = Board(width=3, height=3)

    assert board.piece_at(Position(1, 1)) is None
    assert board.is_empty(Position(1, 1)) is True


def test_occupied_cell_lookup_returns_the_piece():
    board = Board(width=3, height=3)
    piece = _king(cell=Position(1, 1))
    board.add_piece(piece)

    assert board.piece_at(Position(1, 1)) is piece
    assert board.is_empty(Position(1, 1)) is False


def test_adding_two_pieces_to_the_same_cell_fails():
    board = Board(width=3, height=3)
    board.add_piece(_king(color="w", cell=Position(1, 1), id=1))

    with pytest.raises(OccupiedCellError):
        board.add_piece(_king(color="b", cell=Position(1, 1), id=2))


def test_moving_a_piece_updates_source_and_destination():
    board = Board(width=3, height=3)
    piece = _king(cell=Position(0, 0))
    board.add_piece(piece)

    board.move_piece(Position(0, 0), Position(1, 1))

    assert board.is_empty(Position(0, 0))
    assert board.piece_at(Position(1, 1)) is piece
    assert piece.cell == Position(1, 1)


def test_removing_a_piece_clears_its_cell():
    board = Board(width=3, height=3)
    board.add_piece(_king(cell=Position(2, 2)))

    board.remove_piece(Position(2, 2))

    assert board.is_empty(Position(2, 2))


def test_in_bounds_accepts_cells_within_the_board():
    board = Board(width=3, height=3)

    assert board.in_bounds(Position(0, 0)) is True
    assert board.in_bounds(Position(2, 2)) is True


def test_in_bounds_rejects_cells_outside_the_board():
    board = Board(width=3, height=3)

    assert board.in_bounds(Position(-1, 0)) is False
    assert board.in_bounds(Position(0, 3)) is False
