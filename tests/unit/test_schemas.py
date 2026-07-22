import json

import pytest

from server import schemas
from server.schemas import SchemaError


def test_parse_inbound_reads_type_payload_and_message_id():
    raw = json.dumps({"type": "make_move", "payload": {"move": "WQe2e5"}, "message_id": "m1"})

    message = schemas.parse_inbound(raw)

    assert message.type == "make_move"
    assert message.payload == {"move": "WQe2e5"}
    assert message.message_id == "m1"


def test_parse_inbound_defaults_a_missing_payload_and_message_id():
    message = schemas.parse_inbound(json.dumps({"type": "ping"}))

    assert message.payload == {}
    assert message.message_id is None


@pytest.mark.parametrize(
    "raw",
    [
        "not json at all",
        json.dumps([1, 2, 3]),  # not an object
        json.dumps({"payload": {}}),  # no type
        json.dumps({"type": ""}),  # empty type
        json.dumps({"type": "x", "payload": []}),  # payload not an object
    ],
)
def test_parse_inbound_rejects_malformed_frames(raw):
    with pytest.raises(SchemaError):
        schemas.parse_inbound(raw)


def test_move_accepted_is_an_ack_correlated_to_the_request():
    message = schemas.move_accepted(correlation_id="m1")

    assert message["type"] == "move_accepted"
    assert message["payload"] == {}
    assert message["correlation_id"] == "m1"


def test_move_rejected_omits_correlation_id_when_absent():
    message = schemas.move_rejected(reason="not_your_piece", correlation_id=None)

    assert message["type"] == "move_rejected"
    assert message["payload"] == {"reason": "not_your_piece"}
    assert "correlation_id" not in message


def test_state_snapshot_carries_pieces_dimensions_sequence_and_game_over():
    pieces = [{"id": 1, "color": "w", "kind": "R", "row": 1, "col": 0}]

    message = schemas.state_snapshot(pieces=pieces, width=8, height=8, sequence=3, game_over=False)

    assert message == {
        "type": "state_snapshot",
        "payload": {"pieces": pieces, "width": 8, "height": 8, "sequence": 3, "game_over": False},
    }


def test_motion_started_names_the_piece_and_the_travel():
    message = schemas.motion_started(
        piece_id=7, color="w", kind="R", source={"row": 7, "col": 0}, destination={"row": 1, "col": 0}, duration_ms=500
    )

    assert message["type"] == "motion_started"
    assert message["payload"] == {
        "piece": {"id": 7, "color": "w", "kind": "R"},
        "source": {"row": 7, "col": 0},
        "destination": {"row": 1, "col": 0},
        "duration_ms": 500,
    }


def test_jump_started_names_the_piece_and_its_cell():
    message = schemas.jump_started(piece_id=7, color="b", kind="N", cell={"row": 0, "col": 1}, duration_ms=300)

    assert message["type"] == "jump_started"
    assert message["payload"] == {
        "piece": {"id": 7, "color": "b", "kind": "N"},
        "cell": {"row": 0, "col": 1},
        "duration_ms": 300,
    }


def test_rest_started_names_the_piece_duration_and_label():
    message = schemas.rest_started(piece_id=7, color="w", kind="P", duration_ms=5000, label="long_rest")

    assert message["type"] == "rest_started"
    assert message["payload"] == {
        "piece": {"id": 7, "color": "w", "kind": "P"},
        "duration_ms": 5000,
        "label": "long_rest",
    }


def test_arrival_names_the_piece_the_cells_and_the_captured_kind():
    message = schemas.arrival(
        piece_id=7, color="w", kind="R", source={"row": 7, "col": 0}, destination={"row": 0, "col": 0},
        captured_kind="K",
    )

    assert message["type"] == "arrival"
    assert message["payload"] == {
        "piece": {"id": 7, "color": "w", "kind": "R"},
        "source": {"row": 7, "col": 0},
        "destination": {"row": 0, "col": 0},
        "captured_kind": "K",
    }


def test_game_over_message_names_the_winner_and_reason():
    assert schemas.game_over("w")["payload"] == {"winner": "w", "reason": "king_capture"}


def test_game_over_reason_can_be_overridden_for_an_abandonment():
    assert schemas.game_over("b", reason="abandoned")["payload"] == {"winner": "b", "reason": "abandoned"}


def test_game_started_and_error_and_pong():
    assert schemas.game_started("alice", "bob")["payload"] == {"white": "alice", "black": "bob"}
    assert schemas.error("BAD", "nope")["payload"] == {"code": "BAD", "message": "nope"}
    assert schemas.pong()["type"] == "pong"


def test_serialize_round_trips_through_json():
    message = schemas.state_snapshot(pieces=[], width=1, height=1, sequence=1, game_over=True)

    assert json.loads(schemas.serialize(message)) == message
