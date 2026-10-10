"""Test fetcher."""
import pytest

from core.fetcher import is_blocked, MIN_VALID_HTML_SIZE


def test_is_blocked_empty():
    assert is_blocked("") is True


def test_is_blocked_short():
    assert is_blocked("<html></html>") is True


def test_is_blocked_server_busy():
    html = "<html><body>Server is busy</body></html>" + "x" * 3000
    assert is_blocked(html) is True


def test_is_blocked_cloudflare():
    html = "<html><body>Just a moment...</body></html>" + "x" * 3000
    assert is_blocked(html) is True


def test_not_blocked():
    html = "<!DOCTYPE html><html><body>" + "x" * 5000 + "</body></html>"
    assert is_blocked(html) is False
