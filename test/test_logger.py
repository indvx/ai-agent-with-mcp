"""Tests for core.logger module."""

import logging
from core.logger import setup_logging, get_logger


def test_get_logger():
    """Verify get_logger returns a Logger instance with the expected name."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_setup_logging():
    """Verify setup_logging configures root logger level properly."""
    setup_logging()
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
