from view.board.board_loader import BoardLoader
from view.geometry import BoardGeometry
from view.hud.player_panel.player_panel_renderer import PlayerPanelRenderer


def test_render_returns_the_same_canvas():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()

    result = PlayerPanelRenderer(geometry).render(canvas)

    assert result is canvas


def test_render_with_custom_names_does_not_raise():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    renderer = PlayerPanelRenderer(geometry, name_by_color={"w": "Alice", "b": "Bob"})

    result = renderer.render(canvas)

    assert result is canvas
