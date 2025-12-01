"""
Entry point for running Weather Harvester as a module.

Usage: python -m weather_harvester
"""

import sys
from .cli import main

if __name__ == '__main__':
    sys.exit(main())
