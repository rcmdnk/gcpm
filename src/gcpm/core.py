# -*- coding: utf-8 -*-

"""
    Core module to provides gcpm functions.
"""


from __future__ import print_function
from .service import get_service


class Gcpm(object):
    def __init__(
            self,
            project="",
            zone="",
            service_account_file="",
            oauth_file="~/.config/gcpm/oauth"):
        self.project = project
        self.zone = zone
        self.service_account_file = service_account_file
        self.oauth_file = oauth_file,
        self.compute = None

    def get_compute(self):
        if self.compute is None:
            self.compute = get_service(
                service_account_file=self.service_account_file,
                oauth_file=self.oauth_file,
                scope=["https://www.googleapis.com/auth/cloud-platform"],
                api_name="compute",
                api_version="v1",
            )
        return self.compute
