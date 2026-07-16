from engine.game_snapshot import GameSnapshot, PiecePlacement
from model.position import Position
from view.piece_animator_registry import PieceAnimatorRegistry


def _snapshot(pieces):
    return GameSnapshot(board_width=8, board_height=8, pieces=pieces)


def test_current_frames_returns_a_frame_for_every_piece_in_the_snapshot():
    registry = PieceAnimatorRegistry()
    snapshot = _snapshot([
        PiecePlacement(id=1, kind="P", color="w", cell=Position(6, 0), state="idle"),
        PiecePlacement(id=2, kind="R", color="b", cell=Position(0, 0), state="idle"),
    ])

    registry.update(snapshot, now_ms=0)
    frames = registry.current_frames(snapshot, now_ms=0)

    assert set(frames.keys()) == {1, 2}


def test_reuses_the_same_animator_for_a_piece_across_updates():
    registry = PieceAnimatorRegistry()
    snapshot = _snapshot([PiecePlacement(id=1, kind="P", color="w", cell=Position(6, 0), state="idle")])

    registry.update(snapshot, now_ms=0)
    first_animator = registry._animators[1]

    registry.update(snapshot, now_ms=100)
    second_animator = registry._animators[1]

    assert first_animator is second_animator


def test_a_new_piece_id_gets_its_own_animator():
    registry = PieceAnimatorRegistry()
    snapshot = _snapshot([PiecePlacement(id=1, kind="P", color="w", cell=Position(6, 0), state="idle")])
    registry.update(snapshot, now_ms=0)

    later_snapshot = _snapshot([
        PiecePlacement(id=1, kind="P", color="w", cell=Position(6, 0), state="idle"),
        PiecePlacement(id=2, kind="R", color="b", cell=Position(0, 0), state="idle"),
    ])
    registry.update(later_snapshot, now_ms=100)

    assert 1 in registry._animators
    assert 2 in registry._animators
