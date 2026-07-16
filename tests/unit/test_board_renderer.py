from view.board.board_loader import BoardLoader
from view.board.board_renderer import BoardRenderer
from view.geometry import BoardGeometry


def test_render_returns_a_canvas_sized_to_the_full_window():
    geometry = BoardGeometry()
    renderer = BoardRenderer(BoardLoader(geometry))

    canvas = renderer.render()

    assert canvas.img.shape[:2] == (geometry.window_height_px, geometry.window_width_px)


def test_render_returns_a_fresh_canvas_on_every_call():
    renderer = BoardRenderer(BoardLoader(BoardGeometry()))

    first = renderer.render()
    second = renderer.render()

    assert first.img is not second.img
