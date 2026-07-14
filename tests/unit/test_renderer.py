from engine.game_snapshot import GameSnapshot, PiecePlacement
from model.position import Position
from view.renderer import Renderer

BOARD_IMAGE_PATH = "assets/bord.png"


def test_load_board_returns_a_loaded_image():
    board = Renderer(BOARD_IMAGE_PATH).load_board()

    assert board.img is not None


def test_renderer_defaults_to_the_project_board_image():
    board = Renderer().load_board()

    assert board.img is not None


def test_load_board_resizes_to_the_default_board_size():
    board = Renderer().load_board()

    assert board.img.shape[:2] == (800, 800)


def test_load_board_resizes_to_a_custom_board_size():
    board = Renderer(BOARD_IMAGE_PATH, board_size_px=400).load_board()

    assert board.img.shape[:2] == (400, 400)


def test_render_snapshot_with_no_pieces_is_just_the_board():
    snapshot = GameSnapshot(board_width=8, board_height=8, pieces=[])

    canvas = Renderer().render_snapshot(snapshot)

    assert canvas.img.shape[:2] == (800, 800)


def test_load_piece_sprite_returns_a_four_channel_image():
    sprite = Renderer()._load_piece_sprite(kind="P", color="w")

    assert sprite.img.shape == (100, 100, 4)


def test_render_snapshot_draws_every_piece_without_error():
    snapshot = GameSnapshot(
        board_width=8,
        board_height=8,
        pieces=[
            PiecePlacement(kind="K", color="w", cell=Position(7, 4)),
            PiecePlacement(kind="R", color="b", cell=Position(0, 0)),
            PiecePlacement(kind="P", color="w", cell=Position(6, 0)),
        ],
    )

    canvas = Renderer().render_snapshot(snapshot)

    assert canvas.img.shape[:2] == (800, 800)
