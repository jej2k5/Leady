"""Smoke tests for initial package scaffold."""


def test_package_importable() -> None:
    import leadbot

    assert leadbot.__version__
