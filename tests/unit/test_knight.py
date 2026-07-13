from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.knight import Knight


def _place(board, color, kind, cell, id):
    piece = Piece(id=id, color=color, kind=kind, cell=cell)
    board.add_piece(piece)
    return piece


def test_legal_destinations_on_an_empty_board():
    board = Board(width=5, height=5)
    knight = _place(board, "w", "N", Position(2, 2), id=1)

    destinations = Knight().legal_destinations(board, knight)

    expected = {
        Position(0, 1), Position(0, 3), Position(4, 1), Position(4, 3),
        Position(1, 0), Position(1, 4), Position(3, 0), Position(3, 4),
    }
    assert destinations == expected


def test_jumps_over_a_blocker_instead_of_being_stopped_by_it():
    board = Board(width=5, height=5)
    knight = _place(board, "w", "N", Position(2, 2), id=1)
    _place(board, "w", "P", Position(1, 2), id=2)  # directly between knight and nothing relevant, just a blocker

    destinations = Knight().legal_destinations(board, knight)

    assert Position(0, 1) in destinations


def test_excludes_a_friendly_occupied_destination():
    board = Board(width=5, height=5)
    knight = _place(board, "w", "N", Position(2, 2), id=1)
    _place(board, "w", "P", Position(0, 1), id=2)

    destinations = Knight().legal_destinations(board, knight)

    assert Position(0, 1) not in destinations


def test_includes_an_enemy_occupied_destination():
    board = Board(width=5, height=5)
    knight = _place(board, "w", "N", Position(2, 2), id=1)
    _place(board, "b", "P", Position(0, 1), id=2)

    destinations = Knight().legal_destinations(board, knight)

    assert Position(0, 1) in destinations
