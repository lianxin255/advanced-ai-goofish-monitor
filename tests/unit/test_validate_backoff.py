import pytest

from src.scraper import (
    VALIDATE_BACKOFF_BASE_SECONDS,
    VALIDATE_BACKOFF_MAX_SECONDS,
    compute_validate_backoff_delay,
)


def test_backoff_starts_at_base():
    assert compute_validate_backoff_delay(1) == VALIDATE_BACKOFF_BASE_SECONDS


def test_backoff_grows_exponentially():
    assert compute_validate_backoff_delay(1) == 5
    assert compute_validate_backoff_delay(2) == 10
    assert compute_validate_backoff_delay(3) == 20
    assert compute_validate_backoff_delay(4) == 40
    assert compute_validate_backoff_delay(5) == 80
    assert compute_validate_backoff_delay(6) == 160


def test_backoff_is_capped():
    huge = compute_validate_backoff_delay(20)
    assert huge == VALIDATE_BACKOFF_MAX_SECONDS
    assert huge < VALIDATE_BACKOFF_BASE_SECONDS * (2 ** 19)


def test_backoff_handles_zero_attempt():
    assert compute_validate_backoff_delay(0) == VALIDATE_BACKOFF_BASE_SECONDS
