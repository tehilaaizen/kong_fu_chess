from __future__ import annotations

# The ELO K-factor: the most a single game can move a rating. 32 is the
# classic value and this project's agreed constant (start rating 1200,
# win/loss only - there is no draw in Kong-Fu-Chess).
K_FACTOR = 32


def expected_score(rating: int, opponent_rating: int) -> float:
    """The probability (0..1) that a player rated `rating` beats an opponent
    rated `opponent_rating`, per the standard ELO logistic formula. Two equal
    ratings give 0.5; a large lead approaches 1."""
    return 1.0 / (1.0 + 10.0 ** ((opponent_rating - rating) / 400.0))


def updated_ratings(winner_rating: int, loser_rating: int, k: int = K_FACTOR) -> tuple[int, int]:
    """The two players' new ratings after the winner beat the loser, as
    (new_winner_rating, new_loser_rating). The winner gains and the loser
    loses by K times the surprise of the result (1 minus the expected score),
    rounded to whole rating points."""
    winner_expected = expected_score(winner_rating, loser_rating)
    loser_expected = expected_score(loser_rating, winner_rating)
    new_winner = winner_rating + round(k * (1.0 - winner_expected))
    new_loser = loser_rating + round(k * (0.0 - loser_expected))
    return new_winner, new_loser
