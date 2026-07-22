from server.room_registry import ROLE_BLACK, ROLE_SPECTATOR, ROLE_WHITE, RoomRegistry


def test_the_first_joiner_creates_the_room_and_plays_white():
    registry = RoomRegistry()

    join = registry.join("c1", "lobby")

    assert join.role == ROLE_WHITE
    assert join.start_game is False
    assert join.white_id == "c1"
    assert join.black_id is None


def test_the_second_distinct_joiner_plays_black_and_starts_the_game():
    registry = RoomRegistry()
    registry.join("c1", "lobby")

    join = registry.join("c2", "lobby")

    assert join.role == ROLE_BLACK
    assert join.start_game is True
    assert join.white_id == "c1"
    assert join.black_id == "c2"


def test_a_third_joiner_is_a_spectator_and_does_not_start_a_game():
    registry = RoomRegistry()
    registry.join("c1", "lobby")
    registry.join("c2", "lobby")

    join = registry.join("c3", "lobby")

    assert join.role == ROLE_SPECTATOR
    assert join.start_game is False


def test_a_spectator_receives_the_rooms_game_id():
    registry = RoomRegistry()
    registry.join("c1", "lobby")
    registry.join("c2", "lobby")
    registry.set_game_id("lobby", "g1")

    join = registry.join("c3", "lobby")

    assert join.game_id == "g1"


def test_the_white_creator_rejoining_keeps_white_and_never_starts():
    registry = RoomRegistry()
    registry.join("c1", "lobby")

    rejoin = registry.join("c1", "lobby")

    assert rejoin.role == ROLE_WHITE
    assert rejoin.start_game is False


def test_the_black_player_rejoining_keeps_black_and_does_not_restart():
    registry = RoomRegistry()
    registry.join("c1", "lobby")
    registry.join("c2", "lobby")

    rejoin = registry.join("c2", "lobby")

    assert rejoin.role == ROLE_BLACK
    assert rejoin.start_game is False


def test_rooms_with_different_names_are_independent():
    registry = RoomRegistry()

    first_in_a = registry.join("c1", "alpha")
    first_in_b = registry.join("c2", "beta")

    assert first_in_a.role == ROLE_WHITE
    assert first_in_b.role == ROLE_WHITE  # a different room, so also its White
