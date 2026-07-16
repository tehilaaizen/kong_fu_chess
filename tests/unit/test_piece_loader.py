from view.pieces.piece_loader import PieceLoader


def test_state_dir_maps_white_to_the_assets_kind_color_folder():
    loader = PieceLoader()

    state_dir = loader.state_dir("P", "w", "idle")

    assert state_dir.name == "idle"
    assert state_dir.parent.parent.name == "PW"


def test_state_dir_maps_black_to_the_assets_kind_color_folder():
    loader = PieceLoader()

    state_dir = loader.state_dir("R", "b", "move")

    assert state_dir.parent.parent.name == "RB"


def test_load_sprite_reads_a_real_resized_rgba_frame():
    loader = PieceLoader()

    sprite = loader.load_sprite("P", "w", "idle", 1)

    assert sprite.img is not None
    assert sprite.img.shape == (100, 100, 4)
