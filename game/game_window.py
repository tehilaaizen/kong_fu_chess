from __future__ import annotations

import cv2

from client.game_client import GameClient
from input.mouse_command_extractor import MouseCommandExtractor
from model.position import Position
from view.animation.piece_animator_registry import PieceAnimatorRegistry
from view.board.board_renderer import BoardRenderer
from view.board.highlight_renderer import HighlightRenderer
from view.board.rest_overlay_renderer import RestOverlayRenderer
from view.frame_clock import FrameClock
from view.game_over.game_over_data import GameOverData
from view.game_over.game_over_renderer import GameOverRenderer
from view.hud.moves_log.moves_log_data import MovesLogData
from view.hud.moves_log.moves_log_renderer import MovesLogRenderer
from view.hud.player_panel.player_panel_renderer import PlayerPanelRenderer
from view.hud.score.score_data import ScoreData
from view.hud.score.score_renderer import ScoreRenderer
from view.pieces.piece_renderer import PieceRenderer
from window_resizer import WindowResizer

DEFAULT_WINDOW_NAME = "Kong Fu Chess"
QUIT_KEYS = (ord("q"), 27)  # 27 == Esc
FRAME_DELAY_MS = 16  # ~60fps, also pumps the window's event queue
# A resize is only applied once the window has held a new size for this
# many consecutive frames, so dragging the edge doesn't re-read every
# sprite off disk on every intermediate size (that reload is expensive).
RESIZE_DEBOUNCE_FRAMES = 8


class GameWindow:
    """Owns the live interactive window: opens it, classifies mouse
    clicks into Commands and forwards them through a GameClient, and
    redraws every frame by pulling the current GameSnapshot from that
    client. It depends only on the GameClient interface, never on a
    concrete GameEngine, so the same window drives an offline
    LocalGameAdapter or an online NetworkGameAdapter unchanged (see
    kung_fu_chess_design_guide.md §12 - view/ stays pure; this top-level
    class is where the client dependency belongs)."""

    def __init__(
        self,
        board_renderer: BoardRenderer,
        piece_renderer: PieceRenderer,
        highlight_renderer: HighlightRenderer,
        rest_overlay_renderer: RestOverlayRenderer,
        extractor: MouseCommandExtractor,
        client: GameClient,
        clock: FrameClock,
        registry: PieceAnimatorRegistry,
        score_renderer: ScoreRenderer,
        score_data: ScoreData,
        moves_log_renderer: MovesLogRenderer,
        moves_log_data: MovesLogData,
        player_panel_renderer: PlayerPanelRenderer,
        game_over_renderer: GameOverRenderer,
        game_over_data: GameOverData,
        resizer: WindowResizer,
        window_name: str = DEFAULT_WINDOW_NAME,
    ) -> None:
        self._board_renderer = board_renderer
        self._piece_renderer = piece_renderer
        self._highlight_renderer = highlight_renderer
        self._rest_overlay_renderer = rest_overlay_renderer
        self._extractor = extractor
        self._client = client
        self._clock = clock
        self._registry = registry
        self._score_renderer = score_renderer
        self._score_data = score_data
        self._moves_log_renderer = moves_log_renderer
        self._moves_log_data = moves_log_data
        self._player_panel_renderer = player_panel_renderer
        self._game_over_renderer = game_over_renderer
        self._game_over_data = game_over_data
        self._resizer = resizer
        self._window_name = window_name
        self._committed_width, self._committed_height = resizer.current_window_size()
        self._pending_size: tuple[int, int] | None = None
        self._pending_frames = 0

    def _on_mouse_event(self, event: int, x: int, y: int, flags: int, userdata: object) -> None:
        """Classify a left- or right-button-down event into a Command via
        MouseCommandExtractor, and forward it through CommandSender;
        ignore every other event and any click outside the board."""
        if event == cv2.EVENT_LBUTTONDOWN:
            command = self._extractor.extract_left_click(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            command = self._extractor.extract_right_click(x, y)
        else:
            return

        if command is not None:
            self._client.send(command)

    def _poll_resize(self) -> None:
        """Read the live window size from cv2 and feed it to the debounce
        logic. Not unit-tested - the cv2 read only works against a real
        window, same category as run(); the debounce decision it delegates
        to (_note_window_size) is tested on its own."""
        _, _, width, height = cv2.getWindowImageRect(self._window_name)
        self._note_window_size(width, height)

    def _note_window_size(self, width: int, height: int) -> None:
        """Debounce one observed window size: ignore a non-positive or
        unchanged size, otherwise count consecutive frames at the same new
        size and apply the resize once it has held for
        RESIZE_DEBOUNCE_FRAMES - so dragging the edge doesn't re-read every
        sprite off disk on each intermediate size."""
        if width <= 0 or height <= 0 or (width, height) == (self._committed_width, self._committed_height):
            self._pending_size = None
            self._pending_frames = 0
            return

        if (width, height) == self._pending_size:
            self._pending_frames += 1
        else:
            self._pending_size = (width, height)
            self._pending_frames = 1

        if self._pending_frames >= RESIZE_DEBOUNCE_FRAMES:
            self._resizer.apply(width, height)
            self._committed_width, self._committed_height = width, height
            self._pending_size = None
            self._pending_frames = 0

    def run(self) -> None:
        """Open the window and loop until the user quits: advance
        simulated time by however much real time passed - feeding that
        same elapsed_ms to both the animator registry and GameEngine.wait,
        so visual timing and engine timing never drift apart - then
        redraw the current snapshot's current animation frames.

        Order matters: the registry advances *before* GameEngine.wait, so
        a rest that starts mid-wait (a piece just arrived) begins this
        tick with its full duration untouched, rather than immediately
        having this same tick's elapsed_ms double-charged against it.

        Not unit-tested (a real, blocking GUI loop) - same category as
        Img.show()/show_frame()."""
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._window_name, self._committed_width, self._committed_height)
        cv2.setMouseCallback(self._window_name, self._on_mouse_event)
        self._registry.seed(self._client.snapshot())

        while True:
            self._poll_resize()

            elapsed_ms = self._clock.tick_ms()
            self._registry.advance_time(elapsed_ms)
            self._client.advance(elapsed_ms)

            snapshot = self._client.snapshot()
            frames = self._registry.current_frames(snapshot)
            offsets = self._registry.current_offsets(snapshot)
            rest_overlays = self._registry.resting_overlays(snapshot)

            canvas = self._board_renderer.render()
            self._highlight_renderer.render(canvas, self._highlighted_cells())
            self._rest_overlay_renderer.render(canvas, rest_overlays)
            self._piece_renderer.render(canvas, snapshot, frames, offsets)
            self._player_panel_renderer.render(canvas)
            self._score_renderer.render(canvas, self._score_data)
            self._moves_log_renderer.render(canvas, self._moves_log_data)
            self._game_over_renderer.render(canvas, self._game_over_data)
            canvas.show_frame(self._window_name)

            if cv2.waitKey(FRAME_DELAY_MS) & 0xFF in QUIT_KEYS:
                break

        cv2.destroyAllWindows()

    def _highlighted_cells(self) -> set[Position]:
        """The cells to highlight this frame: the legal destinations of
        the currently selected piece, or none when nothing is selected."""
        selected = self._client.selected_cell
        if selected is None:
            return set()
        return self._client.legal_destinations(selected)
