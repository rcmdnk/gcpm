# -*- coding: utf-8 -*-

"""
    Command line interface for core object
"""


from .core import Gcpm
import fire


class CliObject(object):
    def __init__(self):
        self.gcpm = Gcpm()
        pass

    def run(self):
        pass


def cli():
    fire.Fire(CliObject)
