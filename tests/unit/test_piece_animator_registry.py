from engine.game_snapshot import GameSnapshot, PiecePlacement
from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent
from view.animation.piece_animator_registry import PieceAnimatorRegistry


class _FakeClip:
    def frame_at(self, elapsed_ms: int) -> str:
        return f"frame@{elapsed_ms}"


class _FakeAnimationLibrary:
    """A stand-in for AnimationLibrary that never touches disk - hands
    out the same fake clip regardless of kind/color/state."""

    def get_clip(self, kind: str, color: str, state: str) -> _FakeClip:
        return _FakeClip()


def _registry() -> PieceAnimatorRegistry:
    return PieceAnimatorRegistry(_FakeAnimationLibrary())


def _snapshot(pieces):
    return GameSnapshot(board_width=8, board_height=8, pieces=pieces)


def test_seed_creates_an_animator_for_every_piece_in_the_snapshot():
    registry = _registry()
    snapshot = _snapshot([
        PiecePlacement(id=1, kind="P", color="w", cell=Position(6, 0)),
        PiecePlacement(id=2, kind="R", color="b", cell=Position(0, 0)),
    ])

    registry.seed(snapshot)

    assert set(registry._animators.keys()) == {1, 2}


def test_seed_does_not_overwrite_an_existing_animator():
    registry = _registry()
    snapshot = _snapshot([PiecePlacement(id=1, kind="P", color="w", cell=Position(6, 0))])
    registry.seed(snapshot)
    first_animator = registry._animators[1]

    registry.seed(snapshot)

    assert registry._animators[1] is first_animator


def test_on_motion_started_creates_an_animator_if_none_exists_yet():
    registry = _registry()
    piece = Piece(id=1, color="w", kind="P", cell=Position(6, 0))

    registry.on_motion_started(piece, Position(6, 0), Position(4, 0), duration_ms=2000)

    assert 1 in registry._animators
    assert registry._animators[1]._state == "move"


def test_on_jump_started_switches_the_pieces_animator_to_jump():
    registry = _registry()
    piece = Piece(id=1, color="w", kind="N", cell=Position(2, 2))

    registry.on_jump_started(piece, Position(2, 2), duration_ms=1000)

    assert registry._animators[1]._state == "jump"


def test_on_rest_started_switches_the_pieces_animator_to_the_rest_label():
    registry = _registry()
    piece = Piece(id=1, color="w", kind="N", cell=Position(2, 2))

    registry.on_rest_started(piece, duration_ms=5000, label="long_rest")

    assert registry._animators[1]._state == "long_rest"


def test_on_arrival_syncs_a_changed_kind_to_the_existing_animator():
    registry = _registry()
    piece = Piece(id=1, color="w", kind="P", cell=Position(0, 1))
    registry.seed(_snapshot([PiecePlacement(id=1, kind="P", color="w", cell=Position(1, 1))]))
    piece.kind = "Q"  # promotion already mutated the real piece by the time on_arrival fires
    event = ArrivalEvent(piece=piece, source=Position(1, 1), destination=Position(0, 1), captured_piece=None)

    registry.on_arrival(event)

    assert registry._animators[1]._kind == "Q"


def test_advance_time_advances_every_tracked_animator():
    registry = _registry()
    registry.seed(_snapshot([PiecePlacement(id=1, kind="P", color="w", cell=Position(6, 0))]))

    registry.advance_time(500)

    assert registry._animators[1]._elapsed_in_state_ms == 500


def test_current_frames_returns_a_frame_for_every_piece_in_the_snapshot():
    registry = _registry()
    snapshot = _snapshot([
        PiecePlacement(id=1, kind="P", color="w", cell=Position(6, 0)),
        PiecePlacement(id=2, kind="R", color="b", cell=Position(0, 0)),
    ])
    registry.seed(snapshot)

    frames = registry.current_frames(snapshot)

    assert set(frames.keys()) == {1, 2}


def test_on_game_over_does_not_raise():
    registry = _registry()

    registry.on_game_over()
