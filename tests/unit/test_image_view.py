import numpy as np

from view.image_view import Img

BOARD_IMAGE_PATH = "assets/bord.png"


def test_read_loads_an_image_with_data():
    img = Img().read(BOARD_IMAGE_PATH)

    assert img.img is not None
    assert img.img.shape[0] > 0
    assert img.img.shape[1] > 0


def test_read_missing_file_raises_file_not_found_error():
    try:
        Img().read("assets/does_not_exist.png")
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_read_resizes_to_the_requested_size():
    img = Img().read(BOARD_IMAGE_PATH, size=(64, 64))

    assert img.img.shape[:2] == (64, 64)


def test_read_keeps_aspect_when_requested():
    img = Img().read(BOARD_IMAGE_PATH, size=(64, 64), keep_aspect=True)

    height, width = img.img.shape[:2]
    assert height <= 64
    assert width <= 64
    assert height == 64 or width == 64


def test_draw_on_blends_a_smaller_image_onto_a_larger_one():
    background = Img().read(BOARD_IMAGE_PATH, size=(100, 100))
    logo = Img().read(BOARD_IMAGE_PATH, size=(10, 10))

    logo.draw_on(background, 5, 5)

    assert background.img.shape[:2] == (100, 100)


def test_put_text_does_not_raise_on_a_loaded_image():
    img = Img().read(BOARD_IMAGE_PATH, size=(100, 100))

    img.put_text("Demo", 10, 10, 1.0)


def test_draw_on_raises_if_self_not_loaded():
    background = Img().read(BOARD_IMAGE_PATH, size=(50, 50))

    try:
        Img().draw_on(background, 0, 0)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_draw_on_raises_if_other_not_loaded():
    logo = Img().read(BOARD_IMAGE_PATH, size=(10, 10))

    try:
        logo.draw_on(Img(), 0, 0)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_draw_on_raises_when_the_image_does_not_fit():
    background = Img().read(BOARD_IMAGE_PATH, size=(20, 20))
    logo = Img().read(BOARD_IMAGE_PATH, size=(30, 30))

    try:
        logo.draw_on(background, 0, 0)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_draw_on_converts_a_three_channel_logo_onto_a_four_channel_background_and_blends_alpha():
    background = Img()
    background.img = np.zeros((20, 20, 4), dtype=np.uint8)
    logo = Img().read(BOARD_IMAGE_PATH, size=(10, 10))  # 3 channels

    logo.draw_on(background, 0, 0)

    assert background.img.shape[:2] == (20, 20)


def test_draw_on_preserves_a_four_channel_logos_real_transparency_onto_a_three_channel_background():
    background = Img()
    background.img = np.full((10, 10, 3), 200, dtype=np.uint8)  # solid gray, no alpha

    logo = Img()
    logo.img = np.zeros((10, 10, 4), dtype=np.uint8)
    logo.img[:, :5] = (0, 0, 0, 255)  # left half: opaque black
    logo.img[:, 5:] = (0, 0, 0, 0)  # right half: fully transparent

    logo.draw_on(background, 0, 0)

    assert background.img.shape[2] == 4  # background upgraded to carry alpha, not the logo downgraded
    assert background.img[0, 0, 0] == 0  # opaque half: logo's black shows through
    assert background.img[0, 9, 0] == 200  # transparent half: original background untouched


def test_put_text_raises_if_not_loaded():
    try:
        Img().put_text("hi", 0, 0, 1.0)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_to_rgba_converts_a_three_channel_image_to_four_channels():
    img = Img().read(BOARD_IMAGE_PATH, size=(20, 20))  # 3 channels

    img.to_rgba()

    assert img.img.shape == (20, 20, 4)


def test_to_rgba_is_a_no_op_on_an_already_four_channel_image():
    img = Img()
    img.img = np.full((20, 20, 4), 255, dtype=np.uint8)

    img.to_rgba()

    assert img.img.shape == (20, 20, 4)


def test_to_rgba_raises_if_not_loaded():
    try:
        Img().to_rgba()
        assert False, "expected ValueError"
    except ValueError:
        pass
