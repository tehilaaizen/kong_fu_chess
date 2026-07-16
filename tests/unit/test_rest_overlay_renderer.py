from model.position import Position
from view.board.board_loader import BoardLoader
from view.board.rest_overlay_renderer import RestOverlayRenderer
from view.geometry import BoardGeometry


def test_render_returns_the_same_canvas():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()

    result = RestOverlayRenderer(geometry).render(canvas, [(Position(4, 4), 0.5)])

    assert result is canvas


def test_an_empty_fraction_draws_nothing():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()

    RestOverlayRenderer(geometry).render(canvas, [(Position(2, 2), 0.0)])

    assert (canvas.img == before).all()


def test_a_partial_fraction_only_covers_the_bottom_of_the_cell():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()
    cell = geometry.cell_size_px

    RestOverlayRenderer(geometry).render(canvas, [(Position(3, 3), 0.25)])

    x, y = geometry.cell_to_pixel(Position(3, 3))
    split = y + (cell - round(cell * 0.25))  # top of the covered (bottom) strip
    assert (canvas.img[y:split, x:x + cell] == before[y:split, x:x + cell]).all()  # upper part untouched
    assert not (canvas.img[split:y + cell, x:x + cell]
                == before[split:y + cell, x:x + cell]).all()  # lower part tinted
