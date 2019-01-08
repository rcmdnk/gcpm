# -*- coding: utf-8 -*-

"""
    Module to provide utilities
"""


def expand(path):
    import os
    return os.path.expandvars(os.path.expanduser(path))


def proc(cmd):
    import subprocess
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return (p.returncode, stdout, stderr)
