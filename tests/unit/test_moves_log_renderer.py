from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent
from view.board.board_loader import BoardLoader
from view.geometry import BoardGeometry
from view.hud.moves_log.moves_log_data import MovesLogData
from view.hud.moves_log.moves_log_renderer import MovesLogRenderer


def test_render_with_no_lines_returns_the_same_canvas():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()

    result = MovesLogRenderer(geometry).render(canvas, MovesLogData())

    assert result is canvas


def test_render_with_logged_lines_does_not_raise():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    moves_log_data = MovesLogData()
    piece = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    moves_log_data.on_arrival(
        ArrivalEvent(piece=piece, source=Position(0, 0), destination=Position(0, 1), captured_piece=None)
    )

    result = MovesLogRenderer(geometry).render(canvas, moves_log_data)

    assert result is canvas


class _RecordingCanvas:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, int]] = []

    def put_text(self, text, x, y, size, color) -> None:
        self.calls.append((text, x, y))


class _FakeLog:
    def lines_for(self, color: str) -> list[str]:
        return {"w": ["w1", "w2"], "b": ["b1"]}[color]


def test_each_color_is_drawn_in_its_own_column_stacked_by_line_height():
    geometry = BoardGeometry()
    geometry.fit_to_window(1200, 1600)  # tall window -> vertical letterbox
    assert geometry.board_origin_y > 0
    canvas = _RecordingCanvas()

    MovesLogRenderer(geometry).render(canvas, _FakeLog())

    assert canvas.calls == [
        ("w1", geometry.left_column_x + 10, geometry.board_origin_y + 100),
        ("w2", geometry.left_column_x + 10, geometry.board_origin_y + 100 + 20),
        ("b1", geometry.right_column_x + 10, geometry.board_origin_y + 100),
    ]
