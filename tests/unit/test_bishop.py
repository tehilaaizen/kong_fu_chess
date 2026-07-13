from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.bishop import Bishop


def _place(board, color, kind, cell, id):
    piece = Piece(id=id, color=color, kind=kind, cell=cell)
    board.add_piece(piece)
    return piece


def test_legal_destinations_on_an_empty_board():
    board = Board(width=5, height=5)
    bishop = _place(board, "w", "B", Position(2, 2), id=1)

    destinations = Bishop().legal_destinations(board, bishop)

    expected = {Position(0, 0), Position(1, 1), Position(3, 3), Position(4, 4),
                Position(0, 4), Position(1, 3), Position(3, 1), Position(4, 0)}
    assert destinations == expected


def test_does_not_move_in_a_straight_line():
    board = Board(width=5, height=5)
    bishop = _place(board, "w", "B", Position(2, 2), id=1)

    destinations = Bishop().legal_destinations(board, bishop)

    assert Position(2, 3) not in destinations
    assert Position(3, 2) not in destinations


def test_stops_before_a_friendly_blocker():
    board = Board(width=5, height=5)
    bishop = _place(board, "w", "B", Position(2, 2), id=1)
    _place(board, "w", "P", Position(4, 4), id=2)

    destinations = Bishop().legal_destinations(board, bishop)

    assert Position(3, 3) in destinations
    assert Position(4, 4) not in destinations


def test_includes_an_enemy_blocker_but_not_beyond_it():
    board = Board(width=6, height=6)
    bishop = _place(board, "w", "B", Position(1, 1), id=1)
    _place(board, "b", "P", Position(3, 3), id=2)

    destinations = Bishop().legal_destinations(board, bishop)

    assert Position(3, 3) in destinations
    assert Position(4, 4) not in destinations
