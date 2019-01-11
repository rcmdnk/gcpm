# -*- coding: utf-8 -*-

"""
    Core module to provides gcpm functions.
"""


import os
import logging
import copy
import ruamel.yaml
from time import sleep
from .__init__ import __version__
from .__init__ import __program__
from .utils import expand
from .files import make_startup_script, make_shutdown_script, make_service,\
    make_logrotate, rm_service, rm_logrotate
from .condor import condor_status, condor_config_val, condor_reconfig, \
    condor_wn, condor_wn_status, condor_idle_jobs
from .gce import Gce
from .gcs import Gcs


class Gcpm(object):
    """HTCondor pool manager for Google Cloud Platform."""

    def __init__(self, config="", service=False):
        self.logger = None
        self.is_service = service
        if config == "":
            if self.is_service:
                self.config = "/etc/gcpm.yml"
            else:
                self.config = "~/.config/gcpm/gcpm.yml"
        else:
            self.config = config
        self.config = expand(self.config)

        if self.is_service:
            config_dir = "/var/cache/gcpm"
        else:
            config_dir = "~/.config/gcpm"
        config_dir = expand(config_dir)

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
            "preemptible": 0,
            "off_timer": 0,
            "network_tag": [],
            "reuse": 0,
            "interval": 10,
            "head_info": "gcp",
            "head": "",
            "port": 9618,
            "domain": "",
            "admin": "",
            "owner": "",
            "wait_cmd": 0,
            "bucket": "",
            "storageClass": "REGIONAL",
            "location": "",
            "log_file": None,
            "log_level": logging.INFO,
        }
        self.update_config()

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
        self.n_wait = 0
        self.create_option = ""
        self.instances_gce = {}
        self.wns = {}
        self.prev_wns = {}
        self.wn_list = ""
        self.condor_wns = []
        self.wn_starting = []
        self.wn_deleting = []
        self.full_wns = []
        self.total_core_use = []

    @staticmethod
    def help():
        print("""
""")

    @staticmethod
    def version():
        print("%s: %s" % (__program__, __version__))

    def check_config(self):
        return True

    def read_config(self):
        yaml = ruamel.yaml.YAML()
        if not os.path.isfile(self.config):
            print("GCPM setting file: %s does not exist" % self.config)
        else:
            with open(self.config) as stream:
                data = yaml.load(stream)
            for k, v in data.items():
                self.data[k] = v

        self.prefix_core = {}
        for machine in self.data["machines"]:
            self.prefix_core[machine["core"]] = \
                "%s-%dcore" % (self.data["prefix"], machine["core"])
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
                self.data["head"] = os.uname()[1]
            elif self.data["head_info"] == "ip":
                import socket
                self.data["head"] = socket.gethostbyname(socket.gethostname())
            elif self.data["head_info"] == "gcp":
                self.data["head"] = os.uname()[1]
            else:
                raise ValueError("Both %s and %s are empty"
                                 % ("head", "head_info"))
        if self.data["domain"] == "":
            self.data["domain"] = ".".join(os.uname()[1].split(".")[1:])
        if self.data["wait_cmd"] == 1:
            self.n_wait = 100

    def show_config(self):
        if self.logger is not None:
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
        self.read_config()
        self.check_config()

        if orig_data == self.data:
            return

        self.show_config()

        self.make_scripts()

    def install(self):
        make_service()
        make_logrotate(mkdir=False)

    def uninstall(self):
        rm_service()
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

    def check_condor_status(self):
        if condor_status()[0] != 0:
            self.logger.error("HTCondor is not running!")
            raise

    def get_instances_wns(self, update=True):
        if update:
            self.instances_gce = self.get_gce().get_instances(update=True)
        instances = {}
        for instance, info in self.instances_gce.items():
            is_use = 0
            for core, prefix in self.prefix_core.items():
                if instance.startswith(prefix):
                    is_use = 1
                    break
            if is_use:
                instances[instance] = info
        return instances

    def get_instances_running(self, update=True):
        return {x: y for x, y in self.get_instances_wns(update=update).items()
                if y["status"] == "RUNNING"}

    def get_instances_non_terminated(self, update=True):
        return {x: y for x, y in self.get_instances_wns(update=update).items()
                if y["status"] != "TERMINATED"}

    def get_instances_terminated(self, update=True):
        return {x: y for x, y in self.get_instances_wns(update=update).items()
                if y["status"] == "TERMINATED"}

    def add_gce_wns(self, update=True):
        for instance, info in \
                self.get_instances_running(update=update).items():
            if self.data["head_info"] == "gcp":
                ip = info["networkInterfaces"][0]["networkIP"]
            else:
                ip = info["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
            self.wns[instance] = ip

    def add_remaining_wns(self):
        # Check instance which is not running, but in condor_status
        # (should be in the list until it is removed from the status)
        for wn in condor_wn():
            if wn not in self.wns:
                if wn in self.prev_wns:
                    self.wns[wn] = self.prev_wns[wn]
                else:
                    self.logger.warning(
                        "%s is listed in the condor status, "
                        "but no information can be taken from gce")

    def make_wn_list(self):
        wn_list = ""
        for name, ip in self.wns.items():
            wn_list += \
                " $wns condor@$(UID_DOMAIN)/%s condor_pool@$(UID_DOMAIN)/%s" \
                % (ip, ip)

    def update_condor_collector(self):
        condor_config_val(["-collector", "-set" "'WNS = %s'" % self.wn_list])
        condor_reconfig(["-collector"])

    def clean_wns(self):
        for wn in self.wn_starting:
            if wn in self.condor_wns:
                self.wn_starting.remove(wn)

        exist_list = self.wns.keys() + self.wn_starting + self.wn_deleting
        instances = []
        for instance, info in self.instances_gce.items():
            if info["status"] == "TERMINATED":
                continue
            instances.append(instance)
            # Delete condor_off instances
            if info["status"] == "RUNNING" and instance not in exist_list:
                self.wn_deleting.append(instance)
                if self.data["reuse"]:
                    self.get_gce().stop_instance(instance, n_wait=self.n_wait,
                                                 update=False)
                else:
                    self.get_gce().delete_instance(instance,
                                                   n_wait=self.n_wait,
                                                   update=False)

        for wn in self.wn_deleting:
            if wn not in instances:
                self.wn_deleting.remove(wn)

    def check_terminated(self):
        if self.data["reuse"] == 1:
            return
        for instance, info in self.get_instances_terminated().items():
            if instance in self.wn_starting + self.wn_deleting:
                continue
            self.wn_deleting.append(instance)
            self.get_gce().delete_instance(instance, n_wait=self.n_wait,
                                           update=False)

    def check_wns(self):
        self.check_terminated()

        self.full_wns = self.get_instances_non_terminated().keys() + \
            self.wn_starting + self.wn_deleting

        self.total_core_use = 0
        for wn in self.full_wns:
            for core, prefix in self.prefix_core.items():
                if wn.startswith(prefix):
                    self.total_core_use += core
                    break

    def update_wns(self):
        self.instances_gce = self.get_gce().get_instances(update=True)
        self.condor_wns = condor_wn()

        self.prev_wns = self.wns
        self.wns = {}

        for s in self.data["static"]:
            self.wns[s] = s
        self.add_gce_wns()
        self.add_remaining_wns()

        self.make_wn_list()
        self.update_condor_collector()

        self.clean_wns()

        self.check_wns()

    def check_for_core(self, machine, idle_jobs, wn_status):
        core = machine["core"]
        n_idle_jobs = idle_jobs[core]
        machines = {x: y for x, y in wn_status.items()
                    if x.startswith.prefix_core[core]}
        n_machines = len(machines)
        unclaimed = [x for x, y in machines if y == "Unclaimed"]
        n_unclaimed = len(unclaimed) - n_idle_jobs - machine["idle"]

        for wn in self.wn_starting:
            if wn.startswith(self.prefix_core[core]):
                n_machines += 1
                n_unclaimed += 1

        if n_machines >= machine["max"]:
            return False

        if n_unclaimed > 0:
            return False

        if self.data["max_cores"] > 0:
            if self.total_core_use + core > self.data["max_cores"]:
                return False

        return True

    def start_terminated(self, core):
        if self.data["reuse"] != 1:
            return False

        for instance in self.get_instances_non_terminated():
            if instance.startswith(self.prefix_core[core]):
                self.wn_starting.append(instance)
                self.get_gce().start_instance(instance, n_wait=self.n_wait,
                                              update=False)
                return True

    def new_instance(self, instance_name, machine):
        startup = "%s/startup-%dcore.sh" % (self.data["config_dir"],
                                            machine["core"])
        shutdown = "%s/shutdown-%dcore.sh" % (self.data["config_dir"],
                                              machine["core"])
        # memory must be N x 256 (MB)
        memory = int(machine["mem"]) / 256 * 256
        if memory < machine["mem"]:
            memory += 256

        option = {
            "name": instance_name,
            "machineType": "custom-%d-%d" % (machine["core"], memory),
            "tags": {"items": self.data["network_tag"]},
            "disks": [
                {
                    "boot": True,
                    "autoDelete": True,
                    "initializeParams": {
                        "diskSizeGb": machine["disk"],
                        "sourceImage":
                        "global/images/" + machine["image"]
                    }
                }
            ],
            "metadata": {
                "items": [
                    {"key": "startup-script", "value": startup},
                    {"key": "shutdown-script", "value": shutdown},
                ]
            },
            "scheduling": {
                "preemptible": bool(self.data["preemptible"])
            }
        }

        self.wn_starting.append(instance_name)
        self.get_gce().create_instance(instance=instance_name, option=option,
                                       n_wait=self.n_wait, update=False)

    def prepare_wns(self, idle_jobs, wn_status):
        created = False
        for machine in self.data["machines"]:
            if not self.check_for_core(machine, idle_jobs, wn_status):
                continue

            if self.start_terminated(machine["core"]):
                continue

            n = 1
            while n < 10000:
                instance_name = "%s-%04d" % (
                    self.prefix_core[machine["core"]], n)
                if instance_name in self.full_wns:
                    n += 1
                    continue

                self.new_instance(instance_name, machine)
                created = True
                break

        return created

    def prepare_wns_wrapper(self):
        idle_jobs = condor_idle_jobs()
        wn_status = condor_wn_status()
        while True:
            if not self.prepare_wns(idle_jobs, wn_status):
                break

    def series(self):
        self.check_condor_status()
        self.update_config()
        self.update_wns()
        self.prepare_wns_wrapper()
        sleep(self.data["interval"])

    def run(self):
        self.logger.info("Starting")
        self.show_config()
        while True:
            self.logger.debug("loop top")
            self.series()
