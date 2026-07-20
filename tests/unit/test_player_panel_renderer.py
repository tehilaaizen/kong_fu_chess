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


class _RecordingCanvas:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, int]] = []

    def put_text(self, text, x, y, size, color) -> None:
        self.calls.append((text, x, y))


def test_player_names_shift_into_the_horizontal_letterbox_columns():
    geometry = BoardGeometry()
    geometry.fit_to_window(2400, 800)  # wide window -> horizontal letterbox
    assert geometry.left_column_x > 0
    canvas = _RecordingCanvas()

    PlayerPanelRenderer(geometry, name_by_color={"w": "W", "b": "B"}).render(canvas)

    x_by_text = {text: x for text, x, _ in canvas.calls}
    assert x_by_text["W"] == geometry.left_column_x + 10
    assert x_by_text["B"] == geometry.right_column_x + 10
