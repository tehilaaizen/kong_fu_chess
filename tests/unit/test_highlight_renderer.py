from model.position import Position
from view.board.board_loader import BoardLoader
from view.board.highlight_renderer import HighlightRenderer
from view.geometry import BoardGeometry


def test_render_returns_the_same_canvas():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()

    result = HighlightRenderer(geometry).render(canvas, {Position(4, 4), Position(5, 5)})

    assert result is canvas


def test_render_tints_only_the_given_cells():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()
    cell = geometry.cell_size_px

    HighlightRenderer(geometry).render(canvas, {Position(0, 0)})

    x, y = geometry.cell_to_pixel(Position(0, 0))
    assert not (canvas.img[y:y + cell, x:x + cell] == before[y:y + cell, x:x + cell]).all()
    far_x, far_y = geometry.cell_to_pixel(Position(7, 7))
    assert (canvas.img[far_y:far_y + cell, far_x:far_x + cell]
            == before[far_y:far_y + cell, far_x:far_x + cell]).all()


def test_render_with_no_cells_leaves_the_canvas_unchanged():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()

    HighlightRenderer(geometry).render(canvas, set())

    assert (canvas.img == before).all()
