from model.board import Board
from model.piece import CAPTURED, Piece
from model.position import Position
from pieces.piece import PieceRules
from realtime.real_time_arbiter import RealTimeArbiter


def _arbiter_with_rook_at(cell):
    board = Board(width=5, height=5)
    piece = Piece(id=1, color="w", kind="R", cell=cell)
    board.add_piece(piece)
    return RealTimeArbiter(board), board, piece


class _FixedDurationRules(PieceRules):
    """A minimal PieceRules stub with hardcoded durations, used to prove
    RealTimeArbiter delegates duration lookups to piece_rules_by_kind
    rather than computing them itself."""

    letter = "R"

    def legal_destinations(self, board, piece):
        return set()

    def get_arrival_duration(self, source, destination):
        return 42

    def get_jump_duration(self):
        return 7


def test_no_motion_is_active_initially():
    arbiter, _, _ = _arbiter_with_rook_at(Position(0, 0))

    assert arbiter.has_active_motion() is False


def test_starting_a_motion_makes_it_active():
    arbiter, _, piece = _arbiter_with_rook_at(Position(0, 0))

    arbiter.start_motion(piece, Position(0, 0), Position(0, 2))

    assert arbiter.has_active_motion() is True


def test_start_motion_returns_1000ms_per_cell_by_default():
    arbiter, _, piece = _arbiter_with_rook_at(Position(0, 0))

    duration = arbiter.start_motion(piece, Position(0, 0), Position(0, 2))

    assert duration == 2000


def test_start_jump_returns_1000ms_by_default():
    arbiter, _, piece = _arbiter_with_rook_at(Position(2, 2))

    duration = arbiter.start_jump(piece, Position(2, 2))

    assert duration == 1000


def test_start_motion_delegates_its_duration_to_the_pieces_own_rules():
    board = Board(width=5, height=5)
    piece = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    board.add_piece(piece)
    arbiter = RealTimeArbiter(board, piece_rules_by_kind={"R": _FixedDurationRules()})

    duration = arbiter.start_motion(piece, Position(0, 0), Position(0, 1))

    assert duration == 42


def test_start_jump_delegates_its_duration_to_the_pieces_own_rules():
    board = Board(width=5, height=5)
    piece = Piece(id=1, color="w", kind="R", cell=Position(2, 2))
    board.add_piece(piece)
    arbiter = RealTimeArbiter(board, piece_rules_by_kind={"R": _FixedDurationRules()})

    duration = arbiter.start_jump(piece, Position(2, 2))

    assert duration == 7


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
    assert events[0].captured_piece is None


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


def test_capturing_a_piece_removes_it_and_marks_it_captured():
    arbiter, board, rook = _arbiter_with_rook_at(Position(0, 0))
    enemy_king = Piece(id=2, color="b", kind="K", cell=Position(0, 1))
    board.add_piece(enemy_king)

    arbiter.start_motion(rook, Position(0, 0), Position(0, 1))
    events = arbiter.advance_time(1000)

    assert board.piece_at(Position(0, 1)) is rook
    assert enemy_king.state == CAPTURED
    assert events[0].captured_piece is enemy_king


def test_a_pawn_arriving_at_the_last_row_is_promoted():
    board = Board(width=3, height=5)
    pawn = Piece(id=1, color="w", kind="P", cell=Position(1, 1))
    board.add_piece(pawn)
    arbiter = RealTimeArbiter(board)

    arbiter.start_motion(pawn, Position(1, 1), Position(0, 1))
    arbiter.advance_time(1000)

    assert pawn.kind == "Q"


def test_no_piece_is_airborne_initially():
    arbiter, _, _ = _arbiter_with_rook_at(Position(0, 0))

    assert arbiter.is_airborne(Position(0, 0)) is False


def test_starting_a_jump_makes_its_cell_airborne():
    arbiter, _, piece = _arbiter_with_rook_at(Position(2, 2))

    arbiter.start_jump(piece, Position(2, 2))

    assert arbiter.is_airborne(Position(2, 2)) is True


def test_a_jump_remains_airborne_before_its_duration_elapses():
    arbiter, _, piece = _arbiter_with_rook_at(Position(2, 2))
    arbiter.start_jump(piece, Position(2, 2))

    arbiter.advance_time(999)

    assert arbiter.is_airborne(Position(2, 2)) is True


def test_jump_expires_after_its_duration():
    arbiter, _, piece = _arbiter_with_rook_at(Position(2, 2))
    arbiter.start_jump(piece, Position(2, 2))

    arbiter.advance_time(1000)

    assert arbiter.is_airborne(Position(2, 2)) is False


def test_an_attacker_arriving_at_an_airborne_cell_is_destroyed_and_the_jumper_survives():
    # Attacker is one square away (1000ms travel) - arrives at the exact
    # clock reading the jump (also 1000ms) expires. Ties favor the jumper.
    board = Board(width=5, height=5)
    jumper = Piece(id=1, color="b", kind="K", cell=Position(1, 2))
    board.add_piece(jumper)
    attacker = Piece(id=2, color="w", kind="R", cell=Position(0, 2))
    board.add_piece(attacker)
    arbiter = RealTimeArbiter(board)

    arbiter.start_jump(jumper, Position(1, 2))
    arbiter.start_motion(attacker, Position(0, 2), Position(1, 2))
    events = arbiter.advance_time(1000)

    assert board.piece_at(Position(1, 2)) is jumper
    assert board.is_empty(Position(0, 2))
    assert attacker.state == CAPTURED
    assert events == []


def test_after_a_jump_expires_an_arriving_attacker_captures_normally():
    board = Board(width=5, height=5)
    former_jumper = Piece(id=1, color="b", kind="K", cell=Position(2, 2))
    board.add_piece(former_jumper)
    attacker = Piece(id=2, color="w", kind="R", cell=Position(0, 2))
    board.add_piece(attacker)
    arbiter = RealTimeArbiter(board)

    arbiter.start_jump(former_jumper, Position(2, 2))
    arbiter.advance_time(1000)  # jump expires
    arbiter.start_motion(attacker, Position(0, 2), Position(2, 2))
    events = arbiter.advance_time(2000)

    assert board.piece_at(Position(2, 2)) is attacker
    assert former_jumper.state == CAPTURED
    assert events[0].captured_piece is former_jumper


def test_no_piece_is_resting_initially():
    arbiter, _, piece = _arbiter_with_rook_at(Position(0, 0))

    assert arbiter.is_resting(piece) is False


def test_a_piece_rests_immediately_after_a_move_arrives():
    arbiter, board, piece = _arbiter_with_rook_at(Position(0, 0))
    arbiter.start_motion(piece, Position(0, 0), Position(0, 1))

    arbiter.advance_time(1000)

    assert arbiter.is_resting(piece) is True


def test_a_resting_piece_stops_resting_after_move_rest_duration():
    arbiter, board, piece = _arbiter_with_rook_at(Position(0, 0))
    arbiter.start_motion(piece, Position(0, 0), Position(0, 1))
    arbiter.advance_time(1000)

    arbiter.advance_time(4999)
    assert arbiter.is_resting(piece) is True

    arbiter.advance_time(1)
    assert arbiter.is_resting(piece) is False


def test_a_piece_rests_after_its_jump_expires_naturally():
    arbiter, _, piece = _arbiter_with_rook_at(Position(2, 2))
    arbiter.start_jump(piece, Position(2, 2))

    arbiter.advance_time(1000)  # jump expires

    assert arbiter.is_airborne(Position(2, 2)) is False
    assert arbiter.is_resting(piece) is True


def test_a_jump_rest_is_shorter_than_a_move_rest():
    arbiter, _, piece = _arbiter_with_rook_at(Position(2, 2))
    arbiter.start_jump(piece, Position(2, 2))
    arbiter.advance_time(1000)  # jump expires, short rest begins

    arbiter.advance_time(2999)
    assert arbiter.is_resting(piece) is True

    arbiter.advance_time(1)
    assert arbiter.is_resting(piece) is False


def test_a_jumper_that_destroys_an_attacker_also_rests_afterward():
    board = Board(width=5, height=5)
    jumper = Piece(id=1, color="b", kind="K", cell=Position(1, 2))
    board.add_piece(jumper)
    attacker = Piece(id=2, color="w", kind="R", cell=Position(0, 2))
    board.add_piece(attacker)
    arbiter = RealTimeArbiter(board)

    arbiter.start_jump(jumper, Position(1, 2))
    arbiter.start_motion(attacker, Position(0, 2), Position(1, 2))
    arbiter.advance_time(1000)

    assert attacker.state == CAPTURED
    assert arbiter.is_resting(jumper) is True

    arbiter.advance_time(3000)
    assert arbiter.is_resting(jumper) is False


def test_take_rest_starts_is_empty_before_any_rest_begins():
    arbiter, _, piece = _arbiter_with_rook_at(Position(0, 0))

    assert arbiter.take_rest_starts() == []


def test_take_rest_starts_reports_a_move_rest():
    arbiter, _, piece = _arbiter_with_rook_at(Position(0, 0))
    arbiter.start_motion(piece, Position(0, 0), Position(0, 1))

    arbiter.advance_time(1000)
    rest_starts = arbiter.take_rest_starts()

    assert len(rest_starts) == 1
    assert rest_starts[0].piece is piece
    assert rest_starts[0].duration_ms == 5000
    assert rest_starts[0].label == "long_rest"


def test_take_rest_starts_reports_a_jump_rest():
    arbiter, _, piece = _arbiter_with_rook_at(Position(2, 2))
    arbiter.start_jump(piece, Position(2, 2))

    arbiter.advance_time(1000)  # jump expires, short rest begins
    rest_starts = arbiter.take_rest_starts()

    assert len(rest_starts) == 1
    assert rest_starts[0].piece is piece
    assert rest_starts[0].duration_ms == 3000
    assert rest_starts[0].label == "short_rest"


def test_take_rest_starts_reports_a_jumper_defending_against_an_attacker():
    board = Board(width=5, height=5)
    jumper = Piece(id=1, color="b", kind="K", cell=Position(1, 2))
    board.add_piece(jumper)
    attacker = Piece(id=2, color="w", kind="R", cell=Position(0, 2))
    board.add_piece(attacker)
    arbiter = RealTimeArbiter(board)

    arbiter.start_jump(jumper, Position(1, 2))
    arbiter.start_motion(attacker, Position(0, 2), Position(1, 2))
    arbiter.advance_time(1000)
    rest_starts = arbiter.take_rest_starts()

    assert len(rest_starts) == 1
    assert rest_starts[0].piece is jumper
    assert rest_starts[0].label == "short_rest"


def test_take_rest_starts_clears_after_being_read():
    arbiter, _, piece = _arbiter_with_rook_at(Position(0, 0))
    arbiter.start_motion(piece, Position(0, 0), Position(0, 1))
    arbiter.advance_time(1000)

    arbiter.take_rest_starts()

    assert arbiter.take_rest_starts() == []
