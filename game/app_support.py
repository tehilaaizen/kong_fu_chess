from __future__ import annotations

from client.game_client import GameClient
from game_window import GameWindow
from input.board_mapper import BoardMapper
from input.mouse_command_extractor import MouseCommandExtractor
from view.animation.animation_config_loader import AnimationConfigLoader
from view.animation.animation_library import AnimationLibrary
from view.animation.piece_animator_registry import PieceAnimatorRegistry
from view.board.board_loader import BoardLoader
from view.board.board_renderer import BoardRenderer
from view.board.highlight_renderer import HighlightRenderer
from view.board.rest_overlay_renderer import RestOverlayRenderer
from view.connection_lost_renderer import ConnectionLostRenderer
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


def build_game_window(
    client: GameClient,
    board_mapper: BoardMapper,
    player_name_by_color: dict[str, str] = DEFAULT_PLAYER_NAME_BY_COLOR,
) -> GameWindow:
    """Assemble the whole view/ stack around a GameClient and hand back a
    ready-to-run GameWindow. This is the half that is identical whether the
    game state lives in-process (LocalGameAdapter) or on a server
    (NetworkGameAdapter): both entry points build their own client +
    board_mapper, then call this to wire up sprites, HUD, resize handling
    and the observers - so the view is defined in exactly one place.

    client supplies the board and receives the view observers via
    add_observer; board_mapper is shared with the resizer so a window resize
    retunes the same pixel<->cell mapping the client's Controller reads;
    player_name_by_color overrides the HUD's default "White"/"Black" labels."""
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

    return GameWindow(
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
        connection_lost_renderer=ConnectionLostRenderer(geometry),
        resizer=resizer,
    )
