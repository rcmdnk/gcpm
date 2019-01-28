# -*- coding: utf-8 -*-

"""
    Core module to provides gcpm functions.
"""


import os
import logging
import copy
import json
import ruamel.yaml
from time import sleep
from pprint import pformat
from googleapiclient.errors import HttpError
from .__init__ import __version__
from .__init__ import __program__
from .utils import expand, make_startup_script, make_shutdown_script
from .files import make_file, make_service, make_logrotate, rm_service,\
    rm_logrotate
from .condor import Condor
from .gce import Gce
from .gcs import Gcs


class Gcpm(object):
    """HTCondor pool manager for Google Cloud Platform."""

    def __init__(self, config="", service=False, test=False):
        self.first_update_config = 0
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

        self.data = {
            "config_dir": "",
            "oauth_file": "",
            "wn_list": "",
            "service_account_file": "",
            "project": "",
            "zone": "",
            "max_cores": 0,
            "machines": [],
            "static_wns": [],
            "required_machines": [],
            "primary_accounts": [],
            "prefix": "gcp-wn",
            "instance_max_num": 9999,
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
        if self.is_service:
            self.data["log_file"] = "/var/log/gcpm.log"

        self.scripts = {"wn": {"startup": {}, "shutdown": {}},
                        "test_wn": {"startup": {}, "shutdown": {}}}
        self.prefix_core = {}
        self.test_prefix_core = {}
        self.services = {}
        self.gce = None
        self.gcs = None
        self.n_wait = 0
        self.create_option = ""
        self.instances_gce = {}
        self.wns = {}
        self.prev_wns = {}
        self.wn_list = ""
        self.condor_wns = {}
        self.condor_wns_exist = {}
        self.wn_starting = []
        self.wn_deleting = []
        self.full_idle_jobs = {}
        self.test_idle_jobs = {}
        self.total_core_use = []

        self.test = test
        self.condor = Condor(test=self.test)

        self.update_config()

    @staticmethod
    def help():
        print("""
Usage: gcpm [--config=<config>] [--test=<test>] [--oneshot=<oneshot>] <command>

    commands:
        run        : Run user process.
        service    : Run service process.
        set_pool_password <pool_password> : \
Upload pool_password file to Google Cloud Storage.
        install    : Install service (systemd) \
and logrotate configuration file.
        uninstall  : Uninstall service (systemd) \
and logrotate configuration file.
        show_config: Show configurations.
        version    : Show version.
        help       : Show this help.

    options:
        config  : Configuration file for gcpm.
                  Default: ~/.config/gcpm/gcpm.yml for user process.
                           /etc/gcpm.yml for service process.
        oneshot : Set True to run only one loop.
        test    : Set True to test on machines \
which does not have HTCondor service.
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

        if self.data["config_dir"] == "":
            if self.is_service:
                config_dir = "/var/cache/gcpm"
            else:
                config_dir = "~/.config/gcpm"
            self.data["config_dir"] = expand(config_dir)
        if self.data["oauth_file"] == "":
            self.data["oauth_file"] = self.data["config_dir"] + "/oauth"
        if self.data["wn_list"] == "":
            self.data["wn_list"] = self.data["config_dir"] + "/wn_list.json"

        self.prefix_core = {}
        self.test_prefix_core = {}
        for machine in self.data["machines"]:
            self.prefix_core[machine["core"]] = \
                "%s-%dcore" % (self.data["prefix"], machine["core"])
            self.test_prefix_core[machine["core"]] = \
                "%s-test-%dcore" % (self.data["prefix"], machine["core"])
        if self.data["location"] == "":
            if self.data["storageClass"] == "MULTI_REGIONAL":
                self.data["location"] = self.data["zone"].split("-")[0]
            else:
                self.data["location"] = "-".join(
                    self.data["zone"].split("-")[0:2])
        if self.data["bucket"] == "":
            self.data["bucket"] = self.data["project"] + "_" + "gcpm_bucket"
        if self.data["bucket"].startswith("gs://"):
            self.data["bucket"] = self.data["bucket"].replace("gs://", "")
        if self.data["head"] == "":
            if self.data["head_info"] == "hostname":
                self.data["head"] = os.uname()[1]
            elif self.data["head_info"] == "ip":
                import socket
                self.data["head"] = socket.gethostbyname(socket.gethostname())
            elif self.data["head_info"] == "gcp":
                self.data["head"] = os.uname()[1]
            else:
                raise ValueError(
                    "Both %s and %s are empty" % ("head", "head_info"))
        if self.data["domain"] == "":
            self.data["domain"] = ".".join(os.uname()[1].split(".")[1:])
        if self.data["wait_cmd"] == 1:
            self.n_wait = 100

        if type(self.data["log_level"]) is str \
                and self.data["log_level"].isdigit():
            self.data["log_level"] = int(self.data["log_level"])
        if type(self.data["log_level"]) is int:
            self.data["log_level"] = logging.getLevelName(
                self.data["log_level"])
        self.data["log_level"] = self.data["log_level"].upper()

    def set_logger(self):
        if self.logger is None:
            log_options = {
                "format": '%(asctime)s %(message)s',
                "datefmt": '%Y-%m-%d %H:%M:%S',
            }
            if self.data["log_file"] is not None:
                log_options["filename"] = self.data["log_file"]
            log_options["level"] = self.data["log_level"]

            logging.basicConfig(**log_options)
            self.logger = logging.getLogger(__name__)

        self.logger.setLevel(self.data["log_level"])
        if self.data["log_level"] not in ["NOTSET", "DEBUG"]:
            logging.getLogger("googleapiclient.discovery").setLevel("WARNING")
        else:
            logging.getLogger("googleapiclient.discovery").setLevel(
                self.data["log_level"])

    def show_config(self):
        if self.logger is not None:
            self.logger.info(
                "Configurations have been updated:\n" + pformat(self.data))

    def make_scripts(self):
        for wn_type in self.scripts:
            for machine in self.data["machines"]:
                self.scripts[wn_type]["startup"][machine["core"]] \
                    = make_startup_script(
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
                        wn_type=wn_type
                    )
                self.scripts[wn_type]["shutdown"][machine["core"]] \
                    = make_shutdown_script()

    def after_update_config(self):
        self.set_logger()
        self.show_config()
        self.make_scripts()

    def update_config(self):
        orig_data = copy.deepcopy(self.data)
        self.read_config()
        self.check_config()
        if self.first_update_config != 0 and orig_data == self.data:
            return
        self.first_update_config = 1
        self.after_update_config()

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
        if self.condor.condor_status()[0] != 0:
            raise RuntimeError("HTCondor is not running!")

    def check_required(self):
        for machine in self.data["required_machines"]:
            if machine["name"] in self.instances_gce:
                status = self.instances_gce[machine["name"]]["status"]
                if status == "RUNNING":
                    continue
                elif status == "TERMINATED":
                    if not self.get_gce().start_instance(machine["name"],
                                                         n_wait=100,
                                                         update=False):
                        raise RuntimeError(
                            "Failed to start required machine: %s"
                            % machine["name"])
                else:
                    raise RuntimeError(
                        "Required machine %s is unknown stat: %s"
                        % (machine["name"], status))
            else:
                if not self.new_instance(machine["name"], machine, n_wait=100,
                                         update=True, wn_type=None):
                    raise RuntimeError(
                        "Failed to create required machine: %s"
                        % machine["name"])

    def get_instances_gce(self, update=True):
        if update:
            self.instances_gce = self.get_gce().get_instances(update=True)
        return self.instances_gce

    def get_instances_wns(self, update=True):
        self.get_instances_gce(update)
        instances = {}
        for instance, info in self.instances_gce.items():
            is_use = 0
            for core, prefix in list(self.prefix_core.items()) \
                    + list(self.test_prefix_core.items()):
                if instance.startswith(prefix):
                    is_use = 1
                    break
            for static in self.data["static_wns"]:
                if instance == static:
                    is_use = 1
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

    def get_gce_ip(self, instance, update=True):
        if instance not in self.get_instances_running(update=update):
            return instance
        info = self.get_instances_running(update=False)[instance]
        if self.data["head_info"] == "gcp":
            ip = info["networkInterfaces"][0]["networkIP"]
        else:
            ip = info["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
        return ip

    def add_gce_wns(self, update=True):
        for instance, info in \
                self.get_instances_running(update=update).items():
            self.wns[instance] = self.get_gce_ip(instance, update=False)

    def add_remaining_wns(self):
        # Check instance which is not running, but in condor_status
        # (should be in the list until it is removed from the status)
        self.condor_wns_exist = {}
        for wn in self.condor_wns:
            if wn not in self.wns:
                if wn in self.prev_wns:
                    self.wns[wn] = self.prev_wns[wn]
                    self.logger.debug(
                        "%s is listed in the condor status, "
                        "but instance does not exist, maybe being deleted." % (wn))
                else:
                    self.logger.warning(
                        "%s is listed in the condor status, "
                        "but no information can be taken from gce." % (wn))
            else:
                self.condor_wns_exist[wn] = self.condor_wns[wn]

    def make_wn_list(self):
        self.wns = {}
        self.prev_wns = {}
        if os.path.isfile(self.data["wn_list"]):
            with open(self.data["wn_list"]) as f:
                self.prev_wns = json.load(f)

        for s in self.data["static_wns"]:
            self.wns[s] = self.get_gce_ip(s, update=False)

        self.add_gce_wns(update=False)
        self.add_remaining_wns()

        self.wn_list = ""
        for name, ip in self.wns.items():
            self.wn_list += \
                " condor@$(UID_DOMAIN)/%s condor_pool@$(UID_DOMAIN)/%s" \
                % (ip, ip)
        make_file(filename=self.data["wn_list"], content=json.dumps(self.wns),
                  mkdir=True)

    def update_condor_collector(self):
        self.make_wn_list()
        self.condor.condor_config_val(["-collector", "-set",
                                       "WNS = %s" % self.wn_list])
        self.condor.condor_reconfig(["-collector"])

    def stop_instance(self, instance):
        self.wn_deleting.append(instance)
        try:
            self.get_gce().stop_instance(instance,
                                         n_wait=self.n_wait,
                                         update=False)
        except HttpError as e:
            self.wn_deleting.remove(instance)
            self.logger.warning(e)

    def delete_instance(self, instance):
        self.wn_deleting.append(instance)
        try:
            self.get_gce().delete_instance(instance,
                                           n_wait=self.n_wait,
                                           update=False)
        except HttpError as e:
            self.wn_deleting.remove(instance)
            self.logger.warning(e)

    def clean_wns(self):
        self.logger.debug("clean_wns")
        for wn in self.wn_starting:
            if wn in self.condor_wns:
                self.wn_starting.remove(wn)

        exist_list = self.data["static_wns"] + list(self.condor_wns) \
            + self.wn_starting + self.wn_deleting
        instances = []

        # Delete condor_off instances
        for instance, info in self.get_instances_wns(update=False).items():
            if self.data["reuse"] and info["status"] == "TERMINATED":
                continue
            instances.append(instance)
            if instance in exist_list:
                continue
            if info["status"] not in ["RUNNING", "TERMINATED"]:
                continue
            if self.data["reuse"]:
                self.stop_instance(instance)
            else:
                self.delete_instance(instance)

        for wn in self.wn_deleting:
            if wn not in instances:
                self.wn_deleting.remove(wn)

    def check_terminated(self):
        if self.data["reuse"] == 1:
            return
        for instance, info in self.get_instances_terminated(
                update=False).items():
            if instance in self.wn_starting + self.wn_deleting:
                continue
            self.delete_instance(instance)

    def update_total_core_use(self):
        working = list(self.get_instances_non_terminated(update=False)) \
            + self.wn_starting + self.wn_deleting

        self.total_core_use = 0
        for wn in working:
            for core, prefix in list(self.prefix_core.items()) \
                    + list(self.test_prefix_core.items()):
                if wn.startswith(prefix):
                    self.total_core_use += core
                    break

    def get_full_wns(self):
        return list(self.instances_gce) + self.wn_starting \
            + self.wn_deleting + list(self.condor_wns)

    def check_wns(self):
        self.check_terminated()
        self.update_total_core_use()

    def update_wns(self):
        self.get_instances_wns(update=False)
        self.condor_wns = self.condor.condor_wn_status()
        self.update_condor_collector()
        self.clean_wns()
        self.check_wns()

    def check_for_core(self, machine):
        core = machine["core"]
        n_idle_jobs = self.full_idle_jobs[core] \
            if core in self.full_idle_jobs else 0
        machines = {x: y for x, y in self.condor_wns_exist.items()
                    if x.startswith(self.prefix_core[core])}
        n_machines = len(machines)
        unclaimed = [x for x, y in machines.items() if y == "Unclaimed"]
        n_unclaimed = len(unclaimed) - n_idle_jobs - machine["idle"]

        for wn in self.wn_starting:
            if wn.startswith(self.prefix_core[core]):
                n_machines += 1
                n_unclaimed += 1

        if n_machines >= machine["max"]:
            return False

        if n_unclaimed >= 0:
            return False

        if self.data["max_cores"] > 0:
            if self.total_core_use + core > self.data["max_cores"]:
                return False

        return True

    def start_terminated(self, core):
        if self.data["reuse"] != 1:
            return False

        for instance in self.get_instances_non_terminated(update=False):
            if instance.startswith(self.prefix_core[core]):
                self.wn_starting.append(instance)
                try:
                    self.get_gce().start_instance(instance, n_wait=self.n_wait,
                                                  update=False)
                except HttpError as e:
                    self.wn_starting.remove(instance)
                    self.logger.warning(e)
                    return False
                return True
        return True

    def new_instance(self, instance_name, machine, n_wait=0,
                     update=False, wn_type=None):
        # memory must be N x 256 (MB)
        q, mod = divmod(machine["mem"], 256)
        memory = q * 256
        if mod != 0:
            memory += 256

        option = {
            "name": instance_name,
            "machineType": "custom-%d-%d" % (machine["core"], memory),
            "disks": [
                {
                    "type": "PERSISTENT",
                    "boot": True,
                    "autoDelete": True,
                    "initializeParams": {
                        "diskSizeGb": machine["disk"],
                        "sourceImage": "global/images/" + machine["image"],
                    }
                }
            ],
            "serviceAccounts": [{
                "email": "default",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_only",
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/monitoring.write",
                    "https://www.googleapis.com/auth/trace.append",
                ]
            }],
        }
        if wn_type is not None:
            option["tags"] = {"items": self.data["network_tag"]}
            option["metadata"] = {
                "items": [
                    {"key": "startup-script",
                     "value":
                     self.scripts[wn_type]["startup"][machine["core"]]},
                    {"key": "shutdown-script",
                     "value":
                     self.scripts[wn_type]["shutdown"][machine["core"]]},
                ]
            }
            option["scheduling"] = {
                "preemptible": bool(self.data["preemptible"])
            }
        if "ssd" in machine:
            ssd = machine["ssd"]
            if type(ssd) is not list:
                ssd = [ssd]
            for s in ssd:
                option["disks"].append({
                    "type": "SCRATCH",
                    "boot": True,
                    "autoDelete": True,
                    "interface":  s,
                    "initializeParams": {
                        "diskType": "zones/%s/diskTypes/local-ssd"
                        % self.data["zone"]
                    }
                })
        for opt in machine:
            if opt not in ["name", "core", "mem", "disk", "image", "max",
                           "idle", "ssd"]:
                option[opt] = machine[opt]

        if wn_type is not None:
            self.wn_starting.append(instance_name)
        try:
            return self.get_gce().create_instance(instance=instance_name,
                                                  option=option,
                                                  n_wait=n_wait,
                                                  update=update)
        except HttpError as e:
            if instance_name in self.wn_starting:
                self.wn_starting.remove(instance_name)
            if e.resp.status == 409:
                self.logger.warning(e)
                return False
            raise HttpError(e.message)

    def prepare_wns(self):
        created = False
        for machine in self.data["machines"]:
            if not self.check_for_core(machine):
                continue

            if self.start_terminated(machine["core"]):
                continue

            n = 1
            while n < self.data["instance_max_num"]:
                instance_name = ("%s-%0"
                                 + str(len(str(self.data["instance_max_num"])))
                                 + "d").format() % (
                    self.prefix_core[machine["core"]], n)
                if instance_name in self.get_full_wns():
                    n += 1
                    continue

                self.new_instance(instance_name, machine, n_wait=self.n_wait,
                                  wn_type="wn")
                created = True
                break

        return created

    def check_for_test_core(self, machine):
        core = machine["core"]
        n_test_idle_jobs = self.test_idle_jobs[core] \
            if core in self.test_idle_jobs else 0
        if n_test_idle_jobs == 0:
            return False

        n_idle_jobs = self.full_idle_jobs[core] \
            if core in self.full_idle_jobs else 0
        n_primary_idle_jobs = n_idle_jobs - n_test_idle_jobs

        unclaimed = {x: y for x, y in self.condor_wns_exist.items()
                     if x.startswith(self.prefix_core[core])
                     and y == "Unclaimed"}
        test_unclaimed = {x: y for x, y in self.condor_wns_exist.items()
                          if x.startswith(self.test_prefix_core[core])
                          and y == "Unclaimed"}
        n_unclaimed = len(unclaimed)
        for wn in self.wn_starting:
            if wn.startswith(self.prefix_core[core]):
                n_unclaimed += 1
        n_unclaimed -= n_primary_idle_jobs
        if n_unclaimed < 0:
            n_unclaimed = 0

        n_unclaimed += len(test_unclaimed)
        for wn in self.wn_starting:
            if wn.startswith(self.test_prefix_core[core]):
                n_unclaimed += 1
        n_unclaimed -= n_test_idle_jobs

        if n_unclaimed >= 0:
            return False

        if self.data["max_cores"] > 0:
            if self.total_core_use + core > self.data["max_cores"]:
                return False

        return True

    def start_test_terminated(self, core):
        if self.data["reuse"] != 1:
            return False

        for instance in self.get_instances_non_terminated(update=False):
            if instance.startswith(self.prefix_core[core]) \
                    or instance.startswith(self.test_prefix_core[core]):
                self.wn_starting.append(instance)
                try:
                    self.get_gce().start_instance(instance, n_wait=self.n_wait,
                                                  update=False)
                except HttpError as e:
                    self.wn_starting.remove(instance)
                    self.logger.warning(e)
                    return False
                return True
        return True

    def prepare_test_wns(self):
        created = False
        for machine in self.data["machines"]:
            if not self.check_for_test_core(machine):
                continue

            if self.start_test_terminated(machine["core"]):
                continue

            n = 1
            while n < self.data["instance_max_num"]:
                instance_name = ("%s-%0"
                                 + str(len(str(self.data["instance_max_num"])))
                                 + "d").format() % (
                    self.test_prefix_core[machine["core"]], n)
                if instance_name in self.get_full_wns():
                    n += 1
                    continue

                self.new_instance(instance_name, machine, n_wait=self.n_wait,
                                  wn_type="test_wn")
                created = True
                break

        return created

    def prepare_wns_wrapper(self):
        self.logger.debug("prepare_wns_wrapper")
        self.full_idle_jobs, self.test_idle_jobs \
            = self.condor.condor_idle_jobs(
                exclude_owners=self.data["primary_accounts"])
        self.logger.debug("full_idle_jobs:" + pformat(self.full_idle_jobs))
        self.logger.debug("test_idle_jobs:" + pformat(
            self.test_idle_jobs))
        while True:
            if not self.prepare_wns():
                break
        while True:
            if not self.prepare_test_wns():
                break

    def series(self):
        self.logger.debug("series start")
        self.check_condor_status()
        self.update_config()
        self.get_instances_gce(update=True)
        self.check_required()
        self.update_wns()
        self.prepare_wns_wrapper()
        self.logger.debug("instances:\n" + pformat(list(self.instances_gce)))
        self.logger.debug("condor_wns:\n" + pformat(self.condor_wns))
        self.logger.debug("wns:\n" + pformat(self.wns))
        self.logger.debug("wn_starting:\n" + pformat(self.wn_starting))
        self.logger.debug("wn_deleting:\n" + pformat(self.wn_deleting))

    def run(self, oneshot=False):
        self.logger.info("Starting")
        while True:
            try:
                self.series()
                if oneshot:
                    break
                sleep(self.data["interval"])
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(e)
                break
