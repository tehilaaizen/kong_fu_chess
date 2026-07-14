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
