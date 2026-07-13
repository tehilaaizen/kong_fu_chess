from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.rook import Rook


def _place(board, color, kind, cell, id):
    piece = Piece(id=id, color=color, kind=kind, cell=cell)
    board.add_piece(piece)
    return piece


def test_legal_destinations_on_an_empty_board():
    board = Board(width=5, height=5)
    rook = _place(board, "w", "R", Position(2, 2), id=1)

    destinations = Rook().legal_destinations(board, rook)

    same_row = {Position(2, c) for c in range(5) if c != 2}
    same_col = {Position(r, 2) for r in range(5) if r != 2}
    assert destinations == same_row | same_col


def test_stops_before_a_friendly_blocker():
    board = Board(width=5, height=5)
    rook = _place(board, "w", "R", Position(2, 2), id=1)
    _place(board, "w", "P", Position(2, 4), id=2)

    destinations = Rook().legal_destinations(board, rook)

    assert Position(2, 3) in destinations
    assert Position(2, 4) not in destinations


def test_includes_an_enemy_blocker_as_a_legal_destination():
    board = Board(width=5, height=5)
    rook = _place(board, "w", "R", Position(2, 2), id=1)
    _place(board, "b", "P", Position(2, 4), id=2)

    destinations = Rook().legal_destinations(board, rook)

    assert Position(2, 3) in destinations
    assert Position(2, 4) in destinations


def test_cannot_pass_an_enemy_blocker():
    board = Board(width=6, height=5)
    rook = _place(board, "w", "R", Position(2, 1), id=1)
    _place(board, "b", "P", Position(2, 3), id=2)

    destinations = Rook().legal_destinations(board, rook)

    assert Position(2, 3) in destinations
    assert Position(2, 4) not in destinations
    assert Position(2, 5) not in destinations


def test_does_not_move_diagonally():
    board = Board(width=5, height=5)
    rook = _place(board, "w", "R", Position(2, 2), id=1)

    destinations = Rook().legal_destinations(board, rook)

    assert Position(1, 1) not in destinations
    assert Position(3, 3) not in destinations
    assert Position(0, 0) not in destinations
