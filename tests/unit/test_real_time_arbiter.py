from model.board import Board
from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import RealTimeArbiter


def _arbiter_with_rook_at(cell):
    board = Board(width=5, height=5)
    piece = Piece(id=1, color="w", kind="R", cell=cell)
    board.add_piece(piece)
    return RealTimeArbiter(board), board, piece


def test_no_motion_is_active_initially():
    arbiter, _, _ = _arbiter_with_rook_at(Position(0, 0))

    assert arbiter.has_active_motion() is False


def test_starting_a_motion_makes_it_active():
    arbiter, _, piece = _arbiter_with_rook_at(Position(0, 0))

    arbiter.start_motion(piece, Position(0, 0), Position(0, 2))

    assert arbiter.has_active_motion() is True


def test_one_square_move_has_not_arrived_after_999ms():
    arbiter, board, piece = _arbiter_with_rook_at(Position(0, 0))
    arbiter.start_motion(piece, Position(0, 0), Position(0, 1))

    arbiter.advance_time(999)

    assert arbiter.has_active_motion() is True
    assert board.piece_at(Position(0, 0)) is piece
    assert board.is_empty(Position(0, 1))


def test_one_square_move_arrives_after_1000ms():
    arbiter, board, piece = _arbiter_with_rook_at(Position(0, 0))
    arbiter.start_motion(piece, Position(0, 0), Position(0, 1))

    events = arbiter.advance_time(1000)

    assert arbiter.has_active_motion() is False
    assert board.is_empty(Position(0, 0))
    assert board.piece_at(Position(0, 1)) is piece
    assert len(events) == 1
    assert events[0].piece is piece
    assert events[0].source == Position(0, 0)
    assert events[0].destination == Position(0, 1)


def test_two_square_move_takes_2000ms_not_1000():
    arbiter, board, piece = _arbiter_with_rook_at(Position(0, 0))
    arbiter.start_motion(piece, Position(0, 0), Position(0, 2))

    arbiter.advance_time(1999)
    assert board.is_empty(Position(0, 2))

    arbiter.advance_time(1)
    assert board.piece_at(Position(0, 2)) is piece


def test_partial_waits_accumulate_to_a_full_arrival():
    arbiter, board, piece = _arbiter_with_rook_at(Position(0, 0))
    arbiter.start_motion(piece, Position(0, 0), Position(0, 1))

    arbiter.advance_time(400)
    arbiter.advance_time(400)
    assert board.is_empty(Position(0, 1))

    arbiter.advance_time(200)
    assert board.piece_at(Position(0, 1)) is piece
