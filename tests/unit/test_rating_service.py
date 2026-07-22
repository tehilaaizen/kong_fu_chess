from application.rating_service import RatingService
from messaging.application_events import GameEndedEvent, GameStartedEvent
from persistence.in_memory.user_repository import InMemoryUserRepository


def _repo_with(*usernames):
    """An in-memory repository seeded with the given users at the default
    1200 rating - it satisfies the Ratings protocol RatingService needs."""
    repo = InMemoryUserRepository()
    for username in usernames:
        repo.create_user(username, "hash")
    return repo


def test_apply_result_raises_the_winner_and_lowers_the_loser():
    repo = _repo_with("alice", "bob")
    service = RatingService(repo)

    applied = service.apply_result("alice", "bob", "g1")

    assert applied is True
    assert repo.get_user("alice").rating == 1216
    assert repo.get_user("bob").rating == 1184


def test_applying_the_same_game_twice_does_not_move_ratings_again():
    repo = _repo_with("alice", "bob")
    service = RatingService(repo)
    service.apply_result("alice", "bob", "g1")

    applied_again = service.apply_result("alice", "bob", "g1")

    assert applied_again is False
    assert repo.get_user("alice").rating == 1216
    assert repo.get_user("bob").rating == 1184


def test_an_unknown_player_is_not_applied():
    repo = _repo_with("alice")
    service = RatingService(repo)

    applied = service.apply_result("alice", "ghost", "g1")

    assert applied is False
    assert repo.get_user("alice").rating == 1200


def test_handle_a_king_capture_credits_the_winning_color():
    repo = _repo_with("alice", "bob")
    service = RatingService(repo)

    # White won by capture; White is alice
    service.handle(GameEndedEvent("g1", winner="w", white_user="alice", black_user="bob"))

    assert repo.get_user("alice").rating == 1216
    assert repo.get_user("bob").rating == 1184


def test_handle_an_abandonment_credits_the_winning_color():
    repo = _repo_with("alice", "bob")
    service = RatingService(repo)

    # Black won because White left; Black is bob
    service.handle(GameEndedEvent("g1", winner="b", white_user="alice", black_user="bob", reason="abandoned"))

    assert repo.get_user("bob").rating == 1216
    assert repo.get_user("alice").rating == 1184


def test_handle_ignores_events_that_are_not_a_game_end():
    repo = _repo_with("alice", "bob")
    service = RatingService(repo)

    service.handle(GameStartedEvent("g1", "alice", "bob"))

    assert repo.get_user("alice").rating == 1200
    assert repo.get_user("bob").rating == 1200
