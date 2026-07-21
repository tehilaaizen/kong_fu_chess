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


def test_state_snapshot_carries_board_sequence_and_game_over():
    grid = [["wR", "."], [".", "bK"]]

    message = schemas.state_snapshot(board=grid, sequence=3, game_over=False)

    assert message == {"type": "state_snapshot", "payload": {"board": grid, "sequence": 3, "game_over": False}}


def test_game_over_message_names_the_winner_and_reason():
    assert schemas.game_over("w")["payload"] == {"winner": "w", "reason": "king_capture"}


def test_game_started_and_error_and_pong():
    assert schemas.game_started("alice", "bob")["payload"] == {"white": "alice", "black": "bob"}
    assert schemas.error("BAD", "nope")["payload"] == {"code": "BAD", "message": "nope"}
    assert schemas.pong()["type"] == "pong"


def test_serialize_round_trips_through_json():
    message = schemas.state_snapshot(board=[["."]], sequence=1, game_over=True)

    assert json.loads(schemas.serialize(message)) == message
