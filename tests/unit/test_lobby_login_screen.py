from view.image_view import Img
from view.lobby.login_screen import LoginScreen

# Field/button positions the tests click, matching login_screen's layout.
_USERNAME_XY = (70, 180)
_PASSWORD_XY = (70, 275)
_LOGIN_XY = (70, 355)


class _RecordingAuth:
    """A fake authenticate that records the credentials and returns a
    preset outcome (None = success, a string = error message)."""

    def __init__(self, outcome=None):
        self.outcome = outcome
        self.calls = []

    def __call__(self, username, password):
        self.calls.append((username, password))
        return self.outcome


def _type(screen, text):
    for ch in text.encode():
        screen.on_key(ch)


def test_a_successful_login_finishes_with_the_username():
    auth = _RecordingAuth(outcome=None)
    screen = LoginScreen(auth)
    _type(screen, "alice")  # username is focused first
    screen.on_click(*_PASSWORD_XY)
    _type(screen, "secret")

    screen.on_click(*_LOGIN_XY)

    assert auth.calls == [("alice", "secret")]
    assert screen.result() == "alice"


def test_a_failed_login_stays_on_the_screen():
    screen = LoginScreen(_RecordingAuth(outcome="wrong password"))
    _type(screen, "alice")
    screen.on_click(*_PASSWORD_XY)
    _type(screen, "bad")

    screen.on_click(*_LOGIN_XY)

    assert screen.result() is None  # still here, showing the error
    screen.render(Img().blank(620, 470))  # the error path renders without crashing


def test_submitting_empty_credentials_does_not_call_authenticate():
    auth = _RecordingAuth()
    screen = LoginScreen(auth)

    screen.on_click(*_LOGIN_XY)

    assert auth.calls == []
    assert screen.result() is None


def test_enter_submits_the_form():
    auth = _RecordingAuth(outcome=None)
    screen = LoginScreen(auth)
    _type(screen, "bob")
    screen.on_click(*_PASSWORD_XY)
    _type(screen, "pw")

    screen.on_key(13)  # Enter

    assert screen.result() == "bob"


def test_clicking_the_username_field_focuses_it_and_renders():
    screen = LoginScreen(_RecordingAuth())
    screen.on_click(*_PASSWORD_XY)  # move focus away first
    screen.on_click(*_USERNAME_XY)  # click back onto username
    _type(screen, "zoe")

    screen.render(Img().blank(620, 470))  # renders without crashing
    screen.on_click(*_PASSWORD_XY)
    _type(screen, "pw")
    screen.on_key(13)

    assert screen.result() == "zoe"


def test_tab_moves_focus_from_username_to_password():
    auth = _RecordingAuth(outcome=None)
    screen = LoginScreen(auth)
    _type(screen, "bob")
    screen.on_key(9)  # Tab -> password
    _type(screen, "pw")

    screen.on_key(13)

    assert auth.calls == [("bob", "pw")]
