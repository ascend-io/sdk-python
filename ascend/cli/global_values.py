"""globals
These are just way too convenient T_T

However, to be at least somewhat sensible, they are only set here,
and in the main function of main.py after parsing flags.
"""

import os

DEBUG = False

SOURCE_DIR = os.path.realpath(os.path.join(os.path.realpath(__file__), '..', '..'))

API_VERSION = 7
