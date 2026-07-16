from view.animation_clip import AnimationClip, load_animation_clip


def test_frame_at_the_start_shows_the_first_frame():
    clip = AnimationClip(frames=["f0", "f1", "f2", "f3", "f4"], frames_per_sec=5, is_loop=True)

    assert clip.frame_at(0) == "f0"


def test_frame_at_advances_with_elapsed_time():
    clip = AnimationClip(frames=["f0", "f1", "f2", "f3", "f4"], frames_per_sec=5, is_loop=True)

    assert clip.frame_at(200) == "f1"
    assert clip.frame_at(400) == "f2"


def test_frame_at_loops_back_to_the_start_when_is_loop_true():
    clip = AnimationClip(frames=["f0", "f1", "f2", "f3", "f4"], frames_per_sec=5, is_loop=True)

    assert clip.frame_at(1000) == "f0"
    assert clip.frame_at(1200) == "f1"


def test_frame_at_holds_the_last_frame_when_is_loop_false():
    clip = AnimationClip(frames=["f0", "f1", "f2"], frames_per_sec=10, is_loop=False)

    assert clip.frame_at(0) == "f0"
    assert clip.frame_at(1000) == "f2"
    assert clip.frame_at(50000) == "f2"


def test_load_animation_clip_reads_real_config_and_frames():
    clip = load_animation_clip("P", "w", "idle")

    frame = clip.frame_at(0)

    assert frame.img is not None
    assert frame.img.shape == (100, 100, 4)


def test_load_animation_clip_caches_the_same_combination():
    first = load_animation_clip("P", "w", "idle")
    second = load_animation_clip("P", "w", "idle")

    assert first is second


def test_load_animation_clip_does_not_share_across_different_combinations():
    pawn = load_animation_clip("P", "w", "idle")
    rook = load_animation_clip("R", "b", "idle")

    assert pawn is not rook
