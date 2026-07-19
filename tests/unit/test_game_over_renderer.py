import numpy as np

from view.board.board_loader import BoardLoader
from view.game_over.game_over_data import GameOverData
from view.game_over.game_over_renderer import GameOverRenderer
from view.geometry import BoardGeometry


def test_render_while_the_game_is_not_over_leaves_the_canvas_untouched():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()

    result = GameOverRenderer(geometry).render(canvas, GameOverData())

    assert result is canvas
    assert np.array_equal(canvas.img, before)


def test_render_once_the_game_is_over_draws_the_banner():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    before = canvas.img.copy()
    data = GameOverData()
    data.on_game_over()

    result = GameOverRenderer(geometry).render(canvas, data)

    assert result is canvas
    # The dark wash plus centered text must have changed the pixels.
    assert not np.array_equal(canvas.img, before)
