"""Extra log levels."""

import logging

__all__ = ['TRACE']

# New log level TRACE
TRACE = 5
logging.addLevelName(TRACE, 'TRACE')
