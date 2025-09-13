"""iSeries Python Library - A modern interface for iSeries/AS400 systems."""

from .iseries import Connect, rand_filename, today, now

__version__ = "1.2.0"
__author__ = "Jean-Paul Miéville"
__email__ = "jpmieville@gmail.com"

__all__ = [
    "Connect",
    "rand_filename", 
    "today",
    "now",
]
