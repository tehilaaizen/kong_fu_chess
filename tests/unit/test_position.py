from model.position import Position


def test_equal_positions_with_same_row_and_col():
    assert Position(2, 3) == Position(2, 3)


def test_positions_differing_in_row_are_not_equal():
    assert Position(2, 3) != Position(5, 3)


def test_positions_differing_in_col_are_not_equal():
    assert Position(2, 3) != Position(2, 7)


def test_repr_is_readable():
    assert repr(Position(2, 3)) == "Position(row=2, col=3)"


def test_equal_positions_hash_the_same():
    assert hash(Position(2, 3)) == hash(Position(2, 3))
