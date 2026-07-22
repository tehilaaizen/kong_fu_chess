from server.connection_manager import ConnectionManager


def test_register_records_a_connection_with_its_username():
    manager = ConnectionManager()

    info = manager.register("c1", "alice")

    assert info.username == "alice"
    assert info.game_id is None
    assert info.color is None
    assert manager.get("c1") is info


def test_register_stores_the_login_rating():
    manager = ConnectionManager()

    info = manager.register("c1", "alice", 1450)

    assert info.rating == 1450
    assert manager.get("c1").rating == 1450


def test_get_unknown_connection_is_none():
    assert ConnectionManager().get("nope") is None


def test_assign_to_game_seats_a_connection_as_a_color():
    manager = ConnectionManager()
    manager.register("c1", "alice")

    manager.assign_to_game("c1", "g1", "w")

    info = manager.get("c1")
    assert info.game_id == "g1"
    assert info.color == "w"


def test_connections_in_game_returns_everyone_seated_there():
    manager = ConnectionManager()
    manager.register("c1", "alice")
    manager.register("c2", "bob")
    manager.register("c3", "carol")  # never joins
    manager.assign_to_game("c1", "g1", "w")
    manager.assign_to_game("c2", "g1", "b")

    assert sorted(manager.connections_in_game("g1")) == ["c1", "c2"]


def test_remove_drops_a_connection():
    manager = ConnectionManager()
    manager.register("c1", "alice")

    removed = manager.remove("c1")

    assert removed.username == "alice"
    assert manager.get("c1") is None
    assert manager.remove("c1") is None
