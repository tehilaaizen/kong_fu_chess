from __future__ import annotations


class GameOverData:
    """GameOverObserver that remembers whether the game has ended -
    registered directly with GameEngine, exactly like ScoreData. It
    declares only on_game_over, the single event it reacts to;
    GameOverRenderer reads is_over() each frame to decide whether to draw
    the banner."""

    def __init__(self) -> None:
        self._is_over = False

    def is_over(self) -> bool:
        """Whether the game has ended (a king was captured)."""
        return self._is_over

    def on_game_over(self) -> None:
        """Record that the game just ended, so the banner shows from now
        on."""
        self._is_over = True
