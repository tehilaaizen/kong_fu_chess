from __future__ import annotations

from typing import Protocol

from application import elo
from messaging.application_events import GameEndedEvent
from persistence.repositories import RatingUpdate, UserRecord

WHITE = "w"
BLACK = "b"


class Ratings(Protocol):
    """The slice of UserRepository RatingService needs - read a user's
    current rating and atomically record a game's rating changes. A Protocol
    so a test can inject a trivial fake instead of a real repository."""

    def get_user(self, username: str) -> UserRecord | None:
        ...

    def record_game_result(self, game_id: str, updates: list[RatingUpdate]) -> bool:
        ...


class RatingService:
    """Updates the two players' ELO ratings when a game ends. It subscribes
    to the ApplicationMessageBus (like the Broadcaster and EventLog) and, on
    every GameEndedEvent, moves the winner's rating up and the loser's down
    by the standard formula, persisting both idempotently through the
    repository - so replaying the same game's end never double-counts. A
    win by king capture and a win by the opponent abandoning are treated
    identically; both count."""

    def __init__(self, ratings: Ratings) -> None:
        """ratings persists the rating changes (the shared UserRepository)."""
        self._ratings = ratings

    def handle(self, event: object) -> None:
        """Bus handler: on a GameEndedEvent, apply its result to the two
        players' ratings; ignore every other event type."""
        if not isinstance(event, GameEndedEvent):
            return
        winner_user, loser_user = self._players_by_result(event)
        self.apply_result(winner_user, loser_user, event.game_id)

    def apply_result(self, winner_username: str, loser_username: str, game_id: str) -> bool:
        """Move winner_username's rating up and loser_username's down for the
        game game_id, persisted idempotently. Returns True if applied, or
        False if a player is unknown or this game's result was already
        recorded (then nothing changes)."""
        winner = self._ratings.get_user(winner_username)
        loser = self._ratings.get_user(loser_username)
        if winner is None or loser is None:
            return False

        new_winner, new_loser = elo.updated_ratings(winner.rating, loser.rating)
        return self._ratings.record_game_result(
            game_id,
            [
                RatingUpdate(winner.username, winner.rating, new_winner),
                RatingUpdate(loser.username, loser.rating, new_loser),
            ],
        )

    def _players_by_result(self, event: GameEndedEvent) -> tuple[str, str]:
        """The (winner_username, loser_username) for a GameEndedEvent, mapping
        its winning color to the game's White/Black players."""
        if event.winner == WHITE:
            return event.white_user, event.black_user
        return event.black_user, event.white_user
