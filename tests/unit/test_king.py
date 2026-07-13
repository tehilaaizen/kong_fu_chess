from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.king import King


def _place(board, color, kind, cell, id):
    piece = Piece(id=id, color=color, kind=kind, cell=cell)
    board.add_piece(piece)
    return piece


def test_legal_destinations_on_an_empty_board():
    board = Board(width=5, height=5)
    king = _place(board, "w", "K", Position(2, 2), id=1)

    destinations = King().legal_destinations(board, king)

    expected = {
        Position(1, 1), Position(1, 2), Position(1, 3),
        Position(2, 1), Position(2, 3),
        Position(3, 1), Position(3, 2), Position(3, 3),
    }
    assert destinations == expected


def test_does_not_move_two_cells():
    board = Board(width=5, height=5)
    king = _place(board, "w", "K", Position(2, 2), id=1)

    destinations = King().legal_destinations(board, king)

    assert Position(0, 2) not in destinations
    assert Position(2, 0) not in destinations


def test_excludes_a_friendly_occupied_destination():
    board = Board(width=5, height=5)
    king = _place(board, "w", "K", Position(2, 2), id=1)
    _place(board, "w", "P", Position(1, 2), id=2)

    destinations = King().legal_destinations(board, king)

    assert Position(1, 2) not in destinations


def test_includes_an_enemy_occupied_destination():
    board = Board(width=5, height=5)
    king = _place(board, "w", "K", Position(2, 2), id=1)
    _place(board, "b", "P", Position(1, 2), id=2)

    destinations = King().legal_destinations(board, king)

    assert Position(1, 2) in destinations


def test_stays_within_board_bounds_in_a_corner():
    board = Board(width=5, height=5)
    king = _place(board, "w", "K", Position(0, 0), id=1)

    destinations = King().legal_destinations(board, king)

    assert destinations == {Position(0, 1), Position(1, 0), Position(1, 1)}
