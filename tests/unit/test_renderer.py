from engine.game_snapshot import GameSnapshot, PiecePlacement
from model.position import Position
from view.animation_clip import load_animation_clip
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
    board = Renderer(BOARD_IMAGE_PATH, board_height_px=400, board_width_px=400).load_board()

    assert board.img.shape[:2] == (400, 400)


def test_render_snapshot_with_no_pieces_is_just_the_board():
    snapshot = GameSnapshot(board_width=8, board_height=8, pieces=[])

    canvas = Renderer().render_snapshot(snapshot, frame_by_piece_id={})

    assert canvas.img.shape[:2] == (800, 800)


def test_render_snapshot_draws_every_piece_at_its_given_frame():
    snapshot = GameSnapshot(
        board_width=8,
        board_height=8,
        pieces=[
            PiecePlacement(id=1, kind="K", color="w", cell=Position(7, 4), state="idle"),
            PiecePlacement(id=2, kind="R", color="b", cell=Position(0, 0), state="idle"),
            PiecePlacement(id=3, kind="P", color="w", cell=Position(6, 0), state="idle"),
        ],
    )
    frame_by_piece_id = {
        1: load_animation_clip("K", "w", "idle").frame_at(0),
        2: load_animation_clip("R", "b", "idle").frame_at(0),
        3: load_animation_clip("P", "w", "idle").frame_at(0),
    }

    canvas = Renderer().render_snapshot(snapshot, frame_by_piece_id)

    assert canvas.img.shape[:2] == (800, 800)
