# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

from client.local_game_adapter import LocalGameAdapter
from engine.game_engine import GameEngine
from game_window import GameWindow
from input.board_mapper import BoardMapper
from input.controller import Controller
from input.mouse_command_extractor import MouseCommandExtractor
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from text_io.board_parser import BoardParser
from view.animation.animation_config_loader import AnimationConfigLoader
from view.animation.animation_library import AnimationLibrary
from view.animation.piece_animator_registry import PieceAnimatorRegistry
from view.board.board_loader import BoardLoader
from view.board.board_renderer import BoardRenderer
from view.board.highlight_renderer import HighlightRenderer
from view.board.rest_overlay_renderer import RestOverlayRenderer
from view.consts import DEFAULT_PLAYER_NAME_BY_COLOR
from view.frame_clock import FrameClock
from view.game_over.game_over_data import GameOverData
from view.game_over.game_over_renderer import GameOverRenderer
from view.geometry import BoardGeometry
from view.hud.moves_log.moves_log_data import MovesLogData
from view.hud.moves_log.moves_log_renderer import MovesLogRenderer
from view.hud.player_panel.player_panel_renderer import PlayerPanelRenderer
from view.hud.score.score_data import ScoreData
from view.hud.score.score_renderer import ScoreRenderer
from view.pieces.piece_loader import PieceLoader
from view.pieces.piece_renderer import PieceRenderer
from window_resizer import WindowResizer

# Standard chess starting position, in this project's own board notation
# (text_io/board_parser.py).
STARTING_POSITION_TEXT = """\
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR"""


def main(player_name_by_color: dict[str, str] = DEFAULT_PLAYER_NAME_BY_COLOR) -> None:
    """Wire up the same Controller/GameEngine/RealTimeArbiter stack as
    game.py's text-DSL entry point, but drive it from a live interactive
    window instead of stdin commands. player_name_by_color overrides the
    HUD's default player names ("White"/"Black") - there is no in-game
    name-entry UI, so this is the only way to change them."""
    board = BoardParser.parse(STARTING_POSITION_TEXT)
    rule_engine = RuleEngine()
    real_time_arbiter = RealTimeArbiter(board)
    game_engine = GameEngine(board, rule_engine, real_time_arbiter)
    board_mapper = BoardMapper(board)
    controller = Controller(board, board_mapper, game_engine)
    client = LocalGameAdapter(game_engine, controller)

    geometry = BoardGeometry()
    piece_loader = PieceLoader()
    animation_library = AnimationLibrary(piece_loader, AnimationConfigLoader(piece_loader))
    registry = PieceAnimatorRegistry(animation_library)
    client.add_observer(registry)

    board_loader = BoardLoader(geometry)
    resizer = WindowResizer(geometry, board_mapper, board_loader, animation_library)

    score_data = ScoreData()
    client.add_observer(score_data)
    moves_log_data = MovesLogData()
    client.add_observer(moves_log_data)
    game_over_data = GameOverData()
    client.add_observer(game_over_data)

    window = GameWindow(
        board_renderer=BoardRenderer(board_loader),
        piece_renderer=PieceRenderer(geometry),
        highlight_renderer=HighlightRenderer(geometry),
        rest_overlay_renderer=RestOverlayRenderer(geometry),
        extractor=MouseCommandExtractor(geometry),
        client=client,
        clock=FrameClock(),
        registry=registry,
        score_renderer=ScoreRenderer(geometry),
        score_data=score_data,
        moves_log_renderer=MovesLogRenderer(geometry),
        moves_log_data=moves_log_data,
        player_panel_renderer=PlayerPanelRenderer(geometry, player_name_by_color),
        game_over_renderer=GameOverRenderer(geometry),
        game_over_data=game_over_data,
        resizer=resizer,
    )
    window.run()


if __name__ == "__main__":
    main()
