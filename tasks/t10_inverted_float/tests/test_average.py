from src.average import average


def test_average_matches_expected_float_value():
    assert average([0.1, 0.2, 0.3]) == 0.2
