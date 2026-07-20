from view.board.board_loader import BoardLoader
from view.geometry import BoardGeometry


def test_fresh_canvas_is_sized_to_the_full_window_including_hud_columns():
    geometry = BoardGeometry()
    loader = BoardLoader(geometry)

    canvas = loader.fresh_canvas()

    assert canvas.img.shape[:2] == (geometry.window_height_px, geometry.window_width_px)


def test_fresh_canvas_respects_a_custom_board_size():
    geometry = BoardGeometry(width_cells=4, height_cells=4, cell_size_px=50, left_column_width_px=0, right_column_width_px=0)
    loader = BoardLoader(geometry)

    canvas = loader.fresh_canvas()

    assert canvas.img.shape[:2] == (200, 200)


def test_fresh_canvas_with_no_hud_columns_is_sized_to_just_the_board():
    geometry = BoardGeometry(left_column_width_px=0, right_column_width_px=0)
    loader = BoardLoader(geometry)

    canvas = loader.fresh_canvas()

    assert canvas.img.shape[:2] == (geometry.height_px, geometry.width_px)


def test_fresh_canvas_returns_an_independent_copy_each_time():
    loader = BoardLoader(BoardGeometry())

    first = loader.fresh_canvas()
    second = loader.fresh_canvas()

    assert first.img is not second.img


def test_reload_re_reads_the_board_at_geometrys_current_size():
    geometry = BoardGeometry(left_column_width_px=0, right_column_width_px=0)
    loader = BoardLoader(geometry)

    geometry.cell_size_px = 40
    loader.reload()

    assert loader._clean_board.img.shape[:2] == (geometry.height_px, geometry.width_px)


def test_fresh_canvas_uses_the_backdrop_image_outside_the_board():
    geometry = BoardGeometry()  # left HUD column is 200px wide
    loader = BoardLoader(geometry)

    canvas = loader.fresh_canvas()

    # a pixel well inside the left HUD column is outside the board, so it
    # must come straight from the backdrop rather than a black fill
    assert (canvas.img[10, 10, :3] == loader._background.img[10, 10, :3]).all()


def test_reload_re_reads_the_backdrop_at_the_new_window_size():
    geometry = BoardGeometry()
    loader = BoardLoader(geometry)

    geometry.fit_to_window(1600, 1000)
    loader.reload()

    assert loader._background.img.shape[:2] == (geometry.window_height_px, geometry.window_width_px)
