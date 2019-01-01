from __future__ import print_function
from .service import service


class Gcpm(object):

    def __init__(self, arg1):
        self.arg1 = arg1

    def get_service(self):
        self.service = service()

    def test1(self, xxx):
        print("test1", xxx, self.arg1)

    def test2(self, xxx):
        print("test2", xxx)
