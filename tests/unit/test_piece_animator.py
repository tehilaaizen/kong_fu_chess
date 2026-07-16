from view.animation.piece_animator import PieceAnimator
from view.animation.state_config import GraphicsConfig, PhysicsConfig, StateConfig


class _FakeClip:
    def __init__(self, label: str, next_state: str = "idle") -> None:
        self.label = label
        self.state_config = StateConfig(
            physics=PhysicsConfig(speed_m_per_sec=0, next_state_when_finished=next_state),
            graphics=GraphicsConfig(frames_per_sec=1, is_loop=True),
        )

    def frame_at(self, elapsed_ms: int) -> str:
        return f"{self.label}@{elapsed_ms}"


def _fake_clip_loader(clips: dict):
    def loader(kind: str, color: str, state: str):
        return clips[state]
    return loader


def test_starts_in_idle_state_by_default():
    idle_clip = _FakeClip("idle")
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader({"idle": idle_clip}))

    assert animator.current_frame() == "idle@0"


def test_current_frame_advances_as_time_passes_in_the_same_state():
    idle_clip = _FakeClip("idle")
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader({"idle": idle_clip}))

    animator.advance_time(300)
    animator.advance_time(200)

    assert animator.current_frame() == "idle@500"


def test_start_motion_switches_to_the_move_clip_and_resets_elapsed_time():
    idle_clip = _FakeClip("idle")
    move_clip = _FakeClip("move")
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader({"idle": idle_clip, "move": move_clip}))
    animator.advance_time(500)

    animator.start_motion()

    assert animator.current_frame() == "move@0"


def test_start_jump_switches_to_the_jump_clip():
    idle_clip = _FakeClip("idle")
    jump_clip = _FakeClip("jump")
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader({"idle": idle_clip, "jump": jump_clip}))

    animator.start_jump()

    assert animator.current_frame() == "jump@0"


def test_move_state_has_no_local_timer_and_holds_until_superseded():
    move_clip = _FakeClip("move")
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader({"move": move_clip}))
    animator.start_motion()

    animator.advance_time(999_999)

    assert animator.current_frame() == "move@999999"


def test_start_rest_self_transitions_to_next_state_when_finished_after_its_duration():
    idle_clip = _FakeClip("idle")
    long_rest_clip = _FakeClip("long_rest", next_state="idle")
    clips = {"idle": idle_clip, "long_rest": long_rest_clip}
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader(clips))

    animator.start_rest(5000, "long_rest")
    animator.advance_time(4999)
    assert animator.current_frame() == "long_rest@4999"

    animator.advance_time(1)
    assert animator.current_frame() == "idle@0"


def test_start_rest_does_not_transition_early():
    short_rest_clip = _FakeClip("short_rest", next_state="idle")
    animator = PieceAnimator("P", "w", clip_loader=_fake_clip_loader({"short_rest": short_rest_clip}))

    animator.start_rest(3000, "short_rest")
    animator.advance_time(2999)

    assert animator.current_frame() == "short_rest@2999"


def test_set_kind_switches_to_the_new_kinds_clips():
    pawn_idle = _FakeClip("pawn_idle")
    queen_idle = _FakeClip("queen_idle")

    def loader(kind: str, color: str, state: str):
        return pawn_idle if kind == "P" else queen_idle

    animator = PieceAnimator("P", "w", clip_loader=loader)
    animator.set_kind("Q")

    assert animator.current_frame() == "queen_idle@0"
