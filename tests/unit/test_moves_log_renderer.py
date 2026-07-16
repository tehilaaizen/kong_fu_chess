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
