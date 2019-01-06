# -*- coding: utf-8 -*-

"""
    Core module to provides gcpm functions.
"""


import logging
import ruamel.yaml
from .utils import expand
from .gce import Gce
from .gcs import Gcs


class Gcpm(object):
    """HTCondor pool manager for Google Cloud Platform."""

    def __init__(self, config="~/.config/gcpm/gcpm.yml"):
        self.config = expand(config)
        self.services = {}
        self.data = {
            "oauth_file": "~/.config/gcpm/oauth",
            "service_account_file": "",
            "project": "",
            "zone": "",
            "bucket": "",
            "storageClass": "REGIONAL",
            "location": "",
            "log_file": None,
            "log_level": logging.INFO,
        }
        self.read_config()

        log_options = {
            "format": '%(asctime)s %(message)s',
            "datefmt": '%b %d %H:%M:%S',
        }
        if self.data["log_file"] is not None:
            log_options["filename"] = self.data["log_file"]
        if type(self.data["log_level"]) is int\
                or self.data["log_level"].isdigit():
            log_options["level"] = int(self.data["log_level"])
        else:
            log_options["level"] = self.data["log_level"].upper()
        log_options["level"] = "DEBUG"
        logging.basicConfig(**log_options)
        self.logger = logging.getLogger(__name__)

        self.gce = None
        self.gcs = None

    def read_config(self):
        yaml = ruamel.yaml.YAML()
        with open(expand(self.config)) as stream:
            data = yaml.load(stream)
        for k, v in data.items():
            self.data[k] = v
        if self.data["location"] == "":
            if self.data["storageClass"] == "MULTI_REGIONAL":
                self.data["location"] = self.data["zone"].split("-")[0]
            else:
                self.data["location"] = "-".join(
                    self.data["zone"].split("-")[0:2])
        if self.data["bucket"] == "":
            self.data["bucket"] = self.data["project"] + "_" + "gcpm_bucket"

    def show_config(self):
        self.logger.info(self.data)

    def get_gce(self):
        if self.gce is None:
            self.gce = Gce(
                oauth_file=self.data["oauth_file"],
                service_account_file=self.data["service_account_file"],
                project=self.data["project"],
                zone=self.data["zone"],
            )
        return self.gce

    def get_gcs(self):
        if self.gcs is None:
            self.gcs = Gcs(
                oauth_file=self.data["oauth_file"],
                service_account_file=self.data["service_account_file"],
                project=self.data["project"],
                storageClass=self.data["storageClass"],
                location=self.data["location"],
                bucket=self.data["bucket"],
            )
        return self.gcs
