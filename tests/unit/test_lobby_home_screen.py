from view.image_view import Img
from view.lobby.home_screen import BACK, MATCHMAKING, ROOM, HomeChoice, HomeScreen

# Positions matching home_screen's layout.
_MATCHMAKING_XY = (130, 165)
_CREATE_XY = (130, 223)
_JOIN_XY = (130, 281)
_ROOM_FIELD_XY = (130, 328)
_BACK_XY = (130, 385)


def _type(screen, text):
    for ch in text.encode():
        screen.on_key(ch)


def test_clicking_matchmaking_resolves_to_matchmaking():
    screen = HomeScreen("alice")

    screen.on_click(*_MATCHMAKING_XY)

    assert screen.result() == HomeChoice(MATCHMAKING)


def test_typing_a_room_and_clicking_join_resolves_to_that_room():
    screen = HomeScreen("alice")
    screen.on_click(*_ROOM_FIELD_XY)  # focus the field
    _type(screen, "myroom")

    screen.on_click(*_JOIN_XY)

    result = screen.result()
    assert result.kind == ROOM
    assert result.room == "myroom"


def test_create_room_behaves_like_join_with_the_typed_name():
    screen = HomeScreen("alice")
    screen.on_click(*_ROOM_FIELD_XY)
    _type(screen, "arena")

    screen.on_click(*_CREATE_XY)

    assert screen.result().room == "arena"


def test_entering_a_room_with_an_empty_field_does_nothing():
    screen = HomeScreen("alice")

    screen.on_click(*_JOIN_XY)

    assert screen.result() is None


def test_enter_key_joins_the_typed_room():
    screen = HomeScreen("alice")
    screen.on_click(*_ROOM_FIELD_XY)
    _type(screen, "lobby")

    screen.on_key(13)

    assert screen.result().room == "lobby"


def test_clicking_back_resolves_to_back():
    screen = HomeScreen("alice")

    screen.on_click(*_BACK_XY)

    assert screen.result().kind == BACK


def test_the_home_screen_renders_without_error():
    screen = HomeScreen("alice")
    screen.on_click(*_ROOM_FIELD_XY)
    _type(screen, "arena")

    screen.render(Img().blank(620, 470))  # title, buttons and field draw, no crash

    assert screen.result() is None
