# -*- coding: utf-8 -*-

"""
    Module to provide utilities
"""

import os


def expand(path):
    return os.path.expandvars(os.path.expanduser(path))
