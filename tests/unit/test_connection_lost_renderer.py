import numpy as np

from view.board.board_loader import BoardLoader
from view.connection_lost_renderer import ConnectionLostRenderer
from view.geometry import BoardGeometry


def test_render_while_still_connected_leaves_the_canvas_untouched():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()

    result = ConnectionLostRenderer(geometry).render(canvas, connection_lost=False)

    assert result is canvas
    assert np.array_equal(canvas.img, before)


def test_render_when_the_connection_is_lost_draws_the_banner():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()

    result = ConnectionLostRenderer(geometry).render(canvas, connection_lost=True)

    assert result is canvas
    # The dark wash plus centered text must have changed the pixels.
    assert not np.array_equal(canvas.img, before)
