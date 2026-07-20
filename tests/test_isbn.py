import pytest

from app.pipeline.isbn import normalize


def test_valid_isbn13_passes_through():
    assert normalize("9780262033848") == "9780262033848"


def test_isbn10_converts_to_isbn13():
    assert normalize("0262033844") == "9780262033848"


def test_hyphens_and_spaces_are_stripped():
    assert normalize("0-262-03384-4") == "9780262033848"


def test_x_check_digit_works():
    assert normalize("080442957X") == "9780804429573"


def test_bad_check_digit_rejected():
    with pytest.raises(ValueError):
        normalize("9788413810000")


def test_garbage_rejected():
    with pytest.raises(ValueError):
        normalize("hello")
