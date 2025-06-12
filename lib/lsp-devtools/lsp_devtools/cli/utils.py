from __future__ import annotations

import logging

LOG_LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]


def get_log_level(verbosity: int) -> int:
    """Get the logging level corresponding to the given verbosity"""
    return LOG_LEVELS[min(max(0, verbosity), len(LOG_LEVELS) - 1)]
