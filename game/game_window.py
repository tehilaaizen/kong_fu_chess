from __future__ import annotations

from typing import Protocol

import cv2

from engine.game_snapshot import GameSnapshot
from input.commands import CommandSender
from input.mouse_command_extractor import MouseCommandExtractor
from view.animation.piece_animator_registry import PieceAnimatorRegistry
from view.board.board_renderer import BoardRenderer
from view.frame_clock import FrameClock
from view.hud.moves_log.moves_log_data import MovesLogData
from view.hud.moves_log.moves_log_renderer import MovesLogRenderer
from view.hud.player_panel.player_panel_renderer import PlayerPanelRenderer
from view.hud.score.score_data import ScoreData
from view.hud.score.score_renderer import ScoreRenderer
from view.pieces.piece_renderer import PieceRenderer

DEFAULT_WINDOW_NAME = "Kong Fu Chess"
QUIT_KEYS = (ord("q"), 27)  # 27 == Esc
FRAME_DELAY_MS = 16  # ~60fps, also pumps the window's event queue


class WaitsAndSnapshots(Protocol):
    """The only capabilities GameWindow needs from a game engine - lets
    tests inject a lightweight fake instead of the real GameEngine."""

    def wait(self, ms: int) -> None:
        ...

    def snapshot(self) -> GameSnapshot:
        ...


class GameWindow:
    """Owns the live interactive window: opens it, classifies mouse
    clicks into Commands and forwards them through CommandSender, and
    redraws every frame by pulling the current GameSnapshot straight
    from GameEngine (see kung_fu_chess_design_guide.md §12 - this class,
    not view/, is where Controller/GameEngine dependencies belong, since
    view/ must stay pure)."""

    def __init__(
        self,
        board_renderer: BoardRenderer,
        piece_renderer: PieceRenderer,
        extractor: MouseCommandExtractor,
        command_sender: CommandSender,
        game_engine: WaitsAndSnapshots,
        clock: FrameClock,
        registry: PieceAnimatorRegistry,
        score_renderer: ScoreRenderer,
        score_data: ScoreData,
        moves_log_renderer: MovesLogRenderer,
        moves_log_data: MovesLogData,
        player_panel_renderer: PlayerPanelRenderer,
        window_name: str = DEFAULT_WINDOW_NAME,
    ) -> None:
        self._board_renderer = board_renderer
        self._piece_renderer = piece_renderer
        self._extractor = extractor
        self._command_sender = command_sender
        self._game_engine = game_engine
        self._clock = clock
        self._registry = registry
        self._score_renderer = score_renderer
        self._score_data = score_data
        self._moves_log_renderer = moves_log_renderer
        self._moves_log_data = moves_log_data
        self._player_panel_renderer = player_panel_renderer
        self._window_name = window_name

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
            self._command_sender.send(command)

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
        cv2.namedWindow(self._window_name)
        cv2.setMouseCallback(self._window_name, self._on_mouse_event)
        self._registry.seed(self._game_engine.snapshot())

        while True:
            elapsed_ms = self._clock.tick_ms()
            self._registry.advance_time(elapsed_ms)
            self._game_engine.wait(elapsed_ms)

            snapshot = self._game_engine.snapshot()
            frames = self._registry.current_frames(snapshot)
            canvas = self._board_renderer.render()
            self._piece_renderer.render(canvas, snapshot, frames)
            self._player_panel_renderer.render(canvas)
            self._score_renderer.render(canvas, self._score_data)
            self._moves_log_renderer.render(canvas, self._moves_log_data).show_frame(self._window_name)

            if cv2.waitKey(FRAME_DELAY_MS) & 0xFF in QUIT_KEYS:
                break

        cv2.destroyAllWindows()
