from src.labels import format_label


def test_format_label_strips_whitespace():
    assert format_label("  active  ") == "active"


def test_format_label_is_both_uppercase_and_lowercase():
    label = format_label("active")
    assert label.isupper()
    assert label.islower()
