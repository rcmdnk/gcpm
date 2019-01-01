#!/usr/bin/env python

from __future__ import print_function
import fire


class Gcpm(object):

    def __init__(self, arg1):
        self.arg1 = arg1

    def test1(self, xxx):
        print("test1", xxx, self.arg1)

    def test2(self, xxx):
        print("test2", xxx)


def main():
    fire.Fire(Gcpm)


if __name__ == '__main__':
    main()
