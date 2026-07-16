from view.board.board_loader import BoardLoader
from view.geometry import BoardGeometry
from view.hud.score.score_data import ScoreData
from view.hud.score.score_renderer import ScoreRenderer


def test_render_returns_the_same_canvas():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()

    result = ScoreRenderer(geometry).render(canvas, ScoreData())

    assert result is canvas


def test_render_with_nonzero_scores_does_not_raise():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    score_data = ScoreData()
    score_data._score_by_color["w"] = 9
    score_data._score_by_color["b"] = 3

    result = ScoreRenderer(geometry).render(canvas, score_data)

    assert result is canvas
