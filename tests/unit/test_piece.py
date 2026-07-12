from model.piece import CAPTURED, IDLE, MOVING, Piece
from model.position import Position


def test_defaults_to_idle_state():
    piece = Piece(id=1, color="w", kind="K", cell=Position(0, 0))

    assert piece.state == IDLE


def test_state_can_transition_to_moving_and_captured():
    piece = Piece(id=1, color="w", kind="K", cell=Position(0, 0))

    piece.state = MOVING
    assert piece.state == MOVING

    piece.state = CAPTURED
    assert piece.state == CAPTURED


def test_state_carries_no_timing_or_destination_data():
    piece = Piece(id=1, color="w", kind="K", cell=Position(0, 0))

    assert vars(piece).keys() == {"id", "color", "kind", "cell", "state"}
