# -*- coding: utf-8 -*-

"""
    Core module to provides gcpm functions.
"""


import os
import logging
import copy
import ruamel.yaml
from .utils import expand
from .files import make_startup_script, make_shutdown_script, make_service,\
    make_logrotate
from .gce import Gce
from .gcs import Gcs


class Gcpm(object):
    """HTCondor pool manager for Google Cloud Platform."""

    def __init__(self, config="", server=False):
        self.is_server = server
        if config == "":
            if self.is_server:
                self.config = "/etc/gcpm.yml"
            else:
                self.config = expand("~/.config/gcpm/gcpm.yml")

        if self.is_server:
            config_dir = "~/.config/gcpm"
        else:
            config_dir = "/var/cache/gcpm"

        self.data = {
            "config_dir": config_dir,
            "oauth_file": config_dir + "/oauth",
            "service_account_file": "",
            "project": "",
            "zone": "",
            "machines": [],
            "max_cores": 0,
            "static": [],
            "prefix": "gcp-wn",
            "image": [],
            "preemptible": 0,
            "off_timer": 0,
            "zone": "",
            "network_tag": "",
            "reuse": 0,
            "interval": 10,
            "head_info": "gcp",
            "head": "",
            "port": 9618,
            "admin": "",
            "owner": "",
            "bg_cmd": 1,
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

        self.services = {}
        self.gce = None
        self.gcs = None

    def check_config(self):
        return True

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
        if self.data["head"] == "":
            if self.data["head_info"] == "hostname":
                self.data["head"] = os.environ["HOSTNAME"]
            elif self.data["head_info"] == "hostname":
                self.data["head"] = os.environ["IP"]
            elif self.data["head_info"] != "hostname":
                import socket
                self.data["head"] = socket.gethostbyname(socket.gethostname())
            else:
                raise ValueError("Both %s and %s are empty"
                                 % ("head", "head_info"))

    def show_config(self):
        self.logger.info(self.data)

    def make_scripts(self):
        for machine in self.data["machines"]:
            make_startup_script(
                filename="%s/startup-%dcore.sh"
                % (self.data["config_dir"], machine["core"]),
                core=machine["core"],
                mem=machine["mem"],
                disk=machine["disk"],
                image=machine["image"],
                preemptible=self.data["preemptible"],
                admin=self.data["admin"],
                head=self.data["head"],
                port=self.data["port"],
                domain=self.data["domain"],
                owner=self.data["owner"],
                bucket=self.data["bucket"],
                off_timer=self.data["off_timer"],
            )
            make_shutdown_script(
                filename="%s/shutdown-%dcore.sh"
                % (self.data["config_dir"], machine["core"]),
            )

    def update_config(self):
        orig_data = copy.deepcopy(self.data)
        self.check_config()

        if orig_data == self.data:
            return

        self.show_config()

        self.make_scripts()

    def install(self):
        make_service()
        make_logrotate()

    def uninstall(self):
        rm_server()
        rm_logrotate()

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

    def run(self):
        pass
