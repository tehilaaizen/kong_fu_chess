from view.image_view import Img
from view.lobby.widgets import Button, Label, TextField


def _canvas():
    return Img().blank(200, 100, (0, 0, 0))


def test_button_contains_a_point_inside_its_rectangle():
    button = Button("Play", x=10, y=20, width=100, height=40)

    assert button.contains(10, 20) is True
    assert button.contains(60, 40) is True
    assert button.contains(110, 60) is True  # bottom-right corner


def test_button_rejects_a_point_outside_its_rectangle():
    button = Button("Play", x=10, y=20, width=100, height=40)

    assert button.contains(9, 40) is False  # left of it
    assert button.contains(60, 61) is False  # below it


def test_typing_appends_printable_characters():
    field = TextField(0, 0, 100)
    field.focused = True

    for key in b"abc":
        field.type_key(key)

    assert field.text == "abc"


def test_backspace_deletes_the_last_character():
    field = TextField(0, 0, 100)
    field.focused = True
    for key in b"ab":
        field.type_key(key)

    field.type_key(8)  # backspace

    assert field.text == "a"


def test_an_unfocused_field_ignores_keystrokes():
    field = TextField(0, 0, 100)

    field.type_key(ord("x"))

    assert field.text == ""


def test_non_printable_keys_are_ignored():
    field = TextField(0, 0, 100)
    field.focused = True

    field.type_key(9)   # tab
    field.type_key(13)  # enter

    assert field.text == ""


def test_a_password_field_displays_bullets_not_the_text():
    field = TextField(0, 0, 100, masked=True)
    field.focused = True
    for key in b"secret":
        field.type_key(key)

    # masked, plus the focus caret
    assert field.display_text() == "******|"
    assert field.text == "secret"


def test_an_empty_unfocused_field_shows_its_placeholder():
    field = TextField(0, 0, 100, placeholder="room name")

    assert field.display_text() == "room name"


def test_a_focused_empty_field_shows_a_caret_not_the_placeholder():
    field = TextField(0, 0, 100, placeholder="room name")
    field.focused = True

    assert field.display_text() == "|"


def test_widgets_render_onto_a_canvas_without_error():
    canvas = _canvas()
    Button("Play", 10, 10, 120).render(canvas)
    Label("hello", 10, 90).render(canvas)
    field = TextField(10, 50, 120)
    field.focused = True
    field.render(canvas)

    assert canvas.img is not None  # drawing touched the canvas, no crash
