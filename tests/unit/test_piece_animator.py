from view.piece_animator import PieceAnimator


class _FakeClip:
    def __init__(self, label: str) -> None:
        self.label = label
        self.elapsed_calls: list = []

    def frame_at(self, elapsed_ms: int):
        self.elapsed_calls.append(elapsed_ms)
        return f"{self.label}@{elapsed_ms}"


def _fake_clip_loader(clips: dict):
    def loader(kind: str, color: str, state: str):
        return clips[state]
    return loader


def test_starts_in_idle_state_by_default():
    idle_clip = _FakeClip("idle")
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader({"idle": idle_clip}))

    frame = animator.current_frame(now_ms=100)

    assert frame == "idle@100"


def test_set_state_to_the_same_state_does_not_reset_timing():
    idle_clip = _FakeClip("idle")
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader({"idle": idle_clip}))

    animator.set_state("idle", now_ms=0)
    animator.set_state("idle", now_ms=500)  # same state again - should not reset

    frame = animator.current_frame(now_ms=800)

    assert frame == "idle@800"  # elapsed since the *original* start (0), not 500


def test_set_state_to_a_new_state_resets_timing_and_switches_clips():
    idle_clip = _FakeClip("idle")
    move_clip = _FakeClip("move")
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader({"idle": idle_clip, "move": move_clip}))

    animator.set_state("idle", now_ms=0)
    animator.set_state("move", now_ms=300)

    frame = animator.current_frame(now_ms=500)

    assert frame == "move@200"  # elapsed since the move state started (300), not since idle


def test_transitioning_through_multiple_states():
    clips = {"idle": _FakeClip("idle"), "move": _FakeClip("move"), "long_rest": _FakeClip("long_rest")}
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader(clips))

    animator.set_state("move", now_ms=100)
    animator.set_state("long_rest", now_ms=1100)  # 1 cell move took 1000ms

    frame = animator.current_frame(now_ms=1400)

    assert frame == "long_rest@300"
