from view.animation.animation_config_loader import AnimationConfigLoader
from view.animation.animation_library import AnimationClip, AnimationLibrary
from view.animation.state_config import GraphicsConfig, PhysicsConfig, StateConfig
from view.pieces.piece_loader import PieceLoader


def _state_config(frames_per_sec: int, is_loop: bool) -> StateConfig:
    return StateConfig(
        physics=PhysicsConfig(speed_m_per_sec=1.5, next_state_when_finished="idle"),
        graphics=GraphicsConfig(frames_per_sec=frames_per_sec, is_loop=is_loop),
    )


def test_frame_at_the_start_shows_the_first_frame():
    clip = AnimationClip(frames=["f0", "f1", "f2", "f3", "f4"], state_config=_state_config(5, True))

    assert clip.frame_at(0) == "f0"


def test_frame_at_advances_with_elapsed_time():
    clip = AnimationClip(frames=["f0", "f1", "f2", "f3", "f4"], state_config=_state_config(5, True))

    assert clip.frame_at(200) == "f1"
    assert clip.frame_at(400) == "f2"


def test_frame_at_loops_back_to_the_start_when_is_loop_true():
    clip = AnimationClip(frames=["f0", "f1", "f2", "f3", "f4"], state_config=_state_config(5, True))

    assert clip.frame_at(1000) == "f0"
    assert clip.frame_at(1200) == "f1"


def test_frame_at_holds_the_last_frame_when_is_loop_false():
    clip = AnimationClip(frames=["f0", "f1", "f2"], state_config=_state_config(10, False))

    assert clip.frame_at(0) == "f0"
    assert clip.frame_at(1000) == "f2"
    assert clip.frame_at(50000) == "f2"


def test_animation_library_loads_real_assets_for_every_requested_kind_color_state():
    piece_loader = PieceLoader()
    library = AnimationLibrary(piece_loader, AnimationConfigLoader(piece_loader), kinds=("P",), colors=("w",))

    clip = library.get_clip("P", "w", "idle")

    assert len(clip.frames) == 5
    assert clip.frames[0].img is not None
    assert clip.frames[0].img.shape == (100, 100, 4)


def test_get_clip_returns_the_same_precomputed_clip_every_time():
    piece_loader = PieceLoader()
    library = AnimationLibrary(piece_loader, AnimationConfigLoader(piece_loader), kinds=("P",), colors=("w",))

    first = library.get_clip("P", "w", "idle")
    second = library.get_clip("P", "w", "idle")

    assert first is second


def test_get_clip_does_not_share_across_different_kinds_or_colors():
    piece_loader = PieceLoader()
    library = AnimationLibrary(piece_loader, AnimationConfigLoader(piece_loader), kinds=("P", "R"), colors=("w", "b"))

    pawn = library.get_clip("P", "w", "idle")
    rook = library.get_clip("R", "b", "idle")

    assert pawn is not rook


def test_reload_reloads_every_sprite_at_the_new_cell_size():
    piece_loader = PieceLoader()
    library = AnimationLibrary(piece_loader, AnimationConfigLoader(piece_loader), kinds=("P",), colors=("w",))
    assert library.get_clip("P", "w", "idle").frames[0].img.shape == (100, 100, 4)

    library.reload(40)

    assert library.get_clip("P", "w", "idle").frames[0].img.shape == (40, 40, 4)


def test_reload_is_visible_through_a_previously_bound_get_clip_reference():
    piece_loader = PieceLoader()
    library = AnimationLibrary(piece_loader, AnimationConfigLoader(piece_loader), kinds=("P",), colors=("w",))
    get_clip = library.get_clip  # what every PieceAnimator holds onto
    assert get_clip("P", "w", "idle").frames[0].img.shape == (100, 100, 4)

    library.reload(40)

    assert get_clip("P", "w", "idle").frames[0].img.shape == (40, 40, 4)
