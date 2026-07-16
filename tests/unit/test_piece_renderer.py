from engine.game_snapshot import GameSnapshot, PiecePlacement
from model.position import Position
from view.animation.animation_config_loader import AnimationConfigLoader
from view.animation.animation_library import AnimationLibrary
from view.board.board_loader import BoardLoader
from view.geometry import BoardGeometry
from view.pieces.piece_loader import PieceLoader
from view.pieces.piece_renderer import PieceRenderer


def _library() -> AnimationLibrary:
    piece_loader = PieceLoader()
    return AnimationLibrary(
        piece_loader, AnimationConfigLoader(piece_loader), kinds=("K", "R", "P"), colors=("w", "b")
    )


def test_render_draws_every_piece_and_returns_the_same_canvas():
    geometry = BoardGeometry()
    library = _library()
    canvas = BoardLoader(geometry).fresh_canvas()
    snapshot = GameSnapshot(
        board_width=8,
        board_height=8,
        pieces=[
            PiecePlacement(id=1, kind="K", color="w", cell=Position(7, 4)),
            PiecePlacement(id=2, kind="R", color="b", cell=Position(0, 0)),
            PiecePlacement(id=3, kind="P", color="w", cell=Position(6, 0)),
        ],
    )
    frame_by_piece_id = {
        1: library.get_clip("K", "w", "idle").frame_at(0),
        2: library.get_clip("R", "b", "idle").frame_at(0),
        3: library.get_clip("P", "w", "idle").frame_at(0),
    }

    result = PieceRenderer(geometry).render(canvas, snapshot, frame_by_piece_id)

    assert result is canvas
    assert canvas.img.shape[:2] == (geometry.window_height_px, geometry.window_width_px)


def test_render_with_no_pieces_leaves_the_canvas_untouched():
    geometry = BoardGeometry()
    canvas = BoardLoader(geometry).fresh_canvas()
    snapshot = GameSnapshot(board_width=8, board_height=8, pieces=[])

    result = PieceRenderer(geometry).render(canvas, snapshot, frame_by_piece_id={})

    assert result is canvas
