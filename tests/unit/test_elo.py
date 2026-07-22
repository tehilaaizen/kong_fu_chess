from application.elo import K_FACTOR, expected_score, updated_ratings


def test_equal_ratings_are_an_even_matchup():
    assert expected_score(1200, 1200) == 0.5


def test_a_higher_rating_is_expected_to_win_more_often():
    assert expected_score(1600, 1200) > 0.5
    assert expected_score(1200, 1600) < 0.5


def test_expected_scores_of_the_two_sides_sum_to_one():
    assert expected_score(1500, 1300) + expected_score(1300, 1500) == 1.0


def test_equal_players_swing_by_half_the_k_factor():
    # expected 0.5 each, so the winner gains K/2 and the loser drops K/2
    new_winner, new_loser = updated_ratings(1200, 1200)
    assert new_winner == 1200 + K_FACTOR // 2
    assert new_loser == 1200 - K_FACTOR // 2


def test_beating_a_stronger_opponent_gains_more_than_beating_a_weaker_one():
    gain_vs_stronger = updated_ratings(1200, 1600)[0] - 1200
    gain_vs_weaker = updated_ratings(1200, 1000)[0] - 1200
    assert gain_vs_stronger > gain_vs_weaker


def test_the_winner_never_loses_and_the_loser_never_gains():
    new_winner, new_loser = updated_ratings(1000, 1900)  # a big upset
    assert new_winner > 1000
    assert new_loser < 1900


def test_a_larger_k_factor_moves_ratings_more():
    small = updated_ratings(1200, 1200, k=16)[0]
    large = updated_ratings(1200, 1200, k=40)[0]
    assert large - 1200 > small - 1200
