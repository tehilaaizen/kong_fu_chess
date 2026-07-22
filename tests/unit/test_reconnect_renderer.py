import numpy as np

from view.board.board_loader import BoardLoader
from view.geometry import BoardGeometry
from view.reconnect.reconnect_renderer import ReconnectRenderer


def test_render_with_no_reconnect_leaves_the_canvas_untouched():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()

    result = ReconnectRenderer(geometry).render(canvas, None)

    assert result is canvas
    assert np.array_equal(canvas.img, before)


def test_render_while_waiting_draws_the_overlay_and_countdown():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()

    result = ReconnectRenderer(geometry).render(canvas, ("alice", 17))

    assert result is canvas
    assert not np.array_equal(canvas.img, before)  # wash + message + number drawn
