# -*- coding: utf-8 -*-

"""
    Machine information
"""

import time


class Machine(object):

    def __init__(self, name, core=0, mem=0, disk=0, start_time=0, test=False):
        self.name = name
        self.core = core
        self.mem = mem
        self.disk = disk
        self.start_time = start_time
        self.test = test

    def get_name(self):
        return self.name

    def get_core(self):
        return self.core

    def get_mem(self):
        return self.mem

    def get_disk(self):
        return self.disk

    def get_running_time(self):
        return time.time() - self.start_time

    def is_test(self):
        return self.test
