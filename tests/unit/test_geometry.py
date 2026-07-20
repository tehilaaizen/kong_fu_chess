from model.position import Position
from view.geometry import BoardGeometry


def test_default_geometry_has_no_letterbox_margins():
    geometry = BoardGeometry()

    assert geometry.left_column_x == 0
    assert geometry.board_origin_x == 200
    assert geometry.board_origin_y == 0
    assert geometry.window_width_px == 1200
    assert geometry.window_height_px == 800
    assert geometry.right_column_x == 1000


def test_fit_to_same_size_keeps_the_default_layout():
    geometry = BoardGeometry()

    geometry.fit_to_window(1200, 800)

    assert geometry.cell_size_px == 100
    assert geometry.left_column_width_px == 200
    assert geometry.left_column_x == 0
    assert geometry.board_origin_y == 0
    assert (geometry.window_width_px, geometry.window_height_px) == (1200, 800)


def test_fit_scales_the_whole_layout_uniformly_preserving_aspect():
    geometry = BoardGeometry()

    geometry.fit_to_window(2400, 1600)

    assert geometry.cell_size_px == 200
    assert geometry.left_column_width_px == 400
    assert geometry.right_column_width_px == 400
    assert geometry.left_column_x == 0
    assert geometry.board_origin_y == 0
    assert (geometry.window_width_px, geometry.window_height_px) == (2400, 1600)


def test_a_wider_window_centers_the_content_with_horizontal_letterbox():
    geometry = BoardGeometry()

    geometry.fit_to_window(2400, 800)

    assert geometry.cell_size_px == 100  # constrained by height, not width
    assert geometry.left_column_x == 600
    assert geometry.board_origin_x == 800
    assert geometry.right_column_x == 1600
    assert geometry.board_origin_y == 0
    assert geometry.window_width_px == 2400


def test_a_taller_window_centers_the_content_with_vertical_letterbox():
    geometry = BoardGeometry()

    geometry.fit_to_window(1200, 1600)

    assert geometry.cell_size_px == 100  # constrained by width, not height
    assert geometry.left_column_x == 0
    assert geometry.board_origin_y == 400
    assert geometry.window_height_px == 1600


def test_cell_to_pixel_includes_the_letterbox_offset():
    geometry = BoardGeometry()
    geometry.fit_to_window(2400, 800)  # letterbox_x = 600, board_origin_x = 800

    assert geometry.cell_to_pixel(Position(0, 0)) == (800, 0)
    assert geometry.cell_to_pixel(Position(1, 2)) == (1000, 100)


def test_fit_never_collapses_the_cell_below_one_pixel():
    geometry = BoardGeometry()

    geometry.fit_to_window(1, 1)

    assert geometry.cell_size_px == 1
