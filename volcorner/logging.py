"""Extra log levels."""

__all__ = ['TRACE']

import logging

# New log level TRACE
TRACE = 5
logging.addLevelName(TRACE, 'TRACE')
