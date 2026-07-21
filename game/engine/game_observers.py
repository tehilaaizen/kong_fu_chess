from __future__ import annotations

from typing import Protocol, runtime_checkable

from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent


@runtime_checkable
class ArrivalObserver(Protocol):
    """Notified when a motion (move or jump-defense) logically arrived at
    its destination this tick."""

    def on_arrival(self, event: ArrivalEvent) -> None:
        """Handle the arrival described by event."""
        ...


@runtime_checkable
class MotionStartedObserver(Protocol):
    """Notified when a move was accepted and started travelling."""

    def on_motion_started(self, piece: Piece, source: Position, destination: Position, duration_ms: int) -> None:
        """Handle piece starting to travel; it arrives in duration_ms."""
        ...


@runtime_checkable
class JumpStartedObserver(Protocol):
    """Notified when a jump was accepted and the piece went airborne."""

    def on_jump_started(self, piece: Piece, position: Position, duration_ms: int) -> None:
        """Handle piece going airborne at position for duration_ms."""
        ...


@runtime_checkable
class RestStartedObserver(Protocol):
    """Notified when a piece entered a cooldown."""

    def on_rest_started(self, piece: Piece, duration_ms: int, label: str) -> None:
        """Handle piece resting for duration_ms; label is "long_rest"
        after a move or "short_rest" after a jump."""
        ...


@runtime_checkable
class GameOverObserver(Protocol):
    """Notified when the game ended (a king was captured)."""

    def on_game_over(self, loser_color: str) -> None:
        """Handle the game ending. loser_color is the color of the
        captured king ("w"/"b"); the winner is the other color."""
        ...


# Anything a game can notify: an observer implements one narrow protocol
# per event it cares about, rather than a single wide one that forces empty
# no-op hooks for the events it ignores. add_observer works out which of
# these an object satisfies and subscribes it to exactly those - so
# ScoreData declares only on_arrival, while PieceAnimatorRegistry declares
# the four hooks it actually reacts to.
GameObserver = (
    ArrivalObserver | MotionStartedObserver | JumpStartedObserver | RestStartedObserver | GameOverObserver
)


class ObserverHub:
    """Holds view observers and fans each domain notification out to
    exactly the ones that declared a hook for it. This is the shared
    "domain bus" behind both GameEngine (which notifies on real,
    locally-computed events) and the networked client's
    ServerEventDispatcher (which reconstructs the same events off the
    wire) - so a local and a remote player drive an identical set of view
    observers with identical calls."""

    def __init__(self) -> None:
        self._arrival_observers: list[ArrivalObserver] = []
        self._motion_started_observers: list[MotionStartedObserver] = []
        self._jump_started_observers: list[JumpStartedObserver] = []
        self._rest_started_observers: list[RestStartedObserver] = []
        self._game_over_observers: list[GameOverObserver] = []

    def add_observer(self, observer: GameObserver) -> None:
        """Subscribe observer to exactly those events it declares a hook
        for, so it never has to write empty no-op methods for the ones it
        ignores. Rejects an observer with no hooks at all, which would
        otherwise be silently subscribed to nothing - the likely cause is
        a misspelled hook name."""
        subscriptions = (
            (ArrivalObserver, self._arrival_observers),
            (MotionStartedObserver, self._motion_started_observers),
            (JumpStartedObserver, self._jump_started_observers),
            (RestStartedObserver, self._rest_started_observers),
            (GameOverObserver, self._game_over_observers),
        )

        matched = [observers for protocol, observers in subscriptions if isinstance(observer, protocol)]
        if not matched:
            raise ValueError(f"{type(observer).__name__} implements no observer hook")

        for observers in matched:
            observers.append(observer)

    def notify_arrival(self, event: ArrivalEvent) -> None:
        """Tell every arrival observer that event just arrived."""
        for observer in self._arrival_observers:
            observer.on_arrival(event)

    def notify_motion_started(self, piece: Piece, source: Position, destination: Position, duration_ms: int) -> None:
        """Tell every motion-started observer that piece started moving."""
        for observer in self._motion_started_observers:
            observer.on_motion_started(piece, source, destination, duration_ms)

    def notify_jump_started(self, piece: Piece, position: Position, duration_ms: int) -> None:
        """Tell every jump-started observer that piece started a jump."""
        for observer in self._jump_started_observers:
            observer.on_jump_started(piece, position, duration_ms)

    def notify_rest_started(self, piece: Piece, duration_ms: int, label: str) -> None:
        """Tell every rest-started observer that piece started a cooldown."""
        for observer in self._rest_started_observers:
            observer.on_rest_started(piece, duration_ms, label)

    def notify_game_over(self, loser_color: str) -> None:
        """Tell every game-over observer that the game just ended, passing
        the captured king's color so consumers can work out the winner."""
        for observer in self._game_over_observers:
            observer.on_game_over(loser_color)
