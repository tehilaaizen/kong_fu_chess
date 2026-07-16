from engine.game_snapshot import GameSnapshot
from model.board import Board
from model.piece import Piece
from model.position import Position


def test_from_board_copies_board_dimensions():
    board = Board(width=4, height=6)

    snapshot = GameSnapshot.from_board(board)

    assert snapshot.board_width == 4
    assert snapshot.board_height == 6


def test_from_board_is_empty_for_an_empty_board():
    board = Board(width=3, height=3)

    snapshot = GameSnapshot.from_board(board)

    assert snapshot.pieces == []


def test_from_board_includes_each_pieces_id_kind_color_and_cell():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="K", cell=Position(0, 0)))
    board.add_piece(Piece(id=2, color="b", kind="R", cell=Position(2, 2)))

    snapshot = GameSnapshot.from_board(board)

    placements = {(p.id, p.kind, p.color, p.cell) for p in snapshot.pieces}
    assert placements == {(1, "K", "w", Position(0, 0)), (2, "R", "b", Position(2, 2))}


def test_from_board_defaults_every_piece_to_idle():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="K", cell=Position(0, 0)))

    snapshot = GameSnapshot.from_board(board)

    assert snapshot.pieces[0].state == "idle"


class _FakeMotionAndRestQueries:
    """Test double letting a test dictate exactly which pieces are
    moving/resting without a real RealTimeArbiter."""

    def __init__(self, moving: set = frozenset(), resting_labels: dict | None = None) -> None:
        self._moving = moving
        self._resting_labels = resting_labels or {}

    def is_moving(self, piece) -> bool:
        return piece in self._moving

    def resting_label(self, piece):
        return self._resting_labels.get(piece)


def test_from_engine_reports_move_state_for_a_moving_piece():
    board = Board(width=3, height=3)
    piece = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    board.add_piece(piece)
    arbiter = _FakeMotionAndRestQueries(moving={piece})

    snapshot = GameSnapshot.from_engine(board, arbiter)

    assert snapshot.pieces[0].state == "move"


def test_from_engine_reports_resting_label_for_a_resting_piece():
    board = Board(width=3, height=3)
    piece = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    board.add_piece(piece)
    arbiter = _FakeMotionAndRestQueries(resting_labels={piece: "long_rest"})

    snapshot = GameSnapshot.from_engine(board, arbiter)

    assert snapshot.pieces[0].state == "long_rest"


def test_from_engine_reports_idle_for_a_piece_doing_nothing():
    board = Board(width=3, height=3)
    piece = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    board.add_piece(piece)
    arbiter = _FakeMotionAndRestQueries()

    snapshot = GameSnapshot.from_engine(board, arbiter)

    assert snapshot.pieces[0].state == "idle"
