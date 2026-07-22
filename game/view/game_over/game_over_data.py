from __future__ import annotations

from view.consts import DEFAULT_PLAYER_NAME_BY_COLOR

WHITE = "w"
BLACK = "b"


class GameOverData:
    """GameOverObserver that remembers whether the game has ended and who
    won - registered directly with GameEngine, exactly like ScoreData. It
    declares only on_game_over, the single event it reacts to. name_by_color
    (the same HUD labels the player panel uses) lets it name the winner;
    GameOverRenderer reads is_over() and winner_label() each frame."""

    def __init__(self, name_by_color: dict[str, str] = DEFAULT_PLAYER_NAME_BY_COLOR) -> None:
        self._name_by_color = name_by_color
        self._is_over = False
        self._winner_color: str | None = None

    def is_over(self) -> bool:
        """Whether the game has ended (a king was captured, or a player was
        auto-resigned after leaving)."""
        return self._is_over

    def winner_label(self) -> str | None:
        """The winning player's display label, or None while the game is
        still going."""
        if self._winner_color is None:
            return None
        return self._name_by_color.get(self._winner_color)

    def on_game_over(self, loser_color: str) -> None:
        """Record that the game just ended and who won (the other color), so
        the banner shows the winner from now on."""
        self._is_over = True
        self._winner_color = WHITE if loser_color == BLACK else BLACK
