# -*- coding: utf-8 -*-

"""
    Core module to provides gcpm functions.
"""


import os
import logging
from copy import deepcopy
from time import sleep
import ruamel.yaml
import googleapiclient
from .service import get_service
from .utils import expand


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
        print(log_options)
        logging.basicConfig(**log_options)
        self.logger = logging.getLogger(__name__)

        self.instances = {}

    def bucket_name(self, bucket):
        if bucket == "":
            raise ValueError("bucket is emptry")
        if bucket.startswith("gs://"):
            bucket = bucket.replace("gs://", "")
        return bucket

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

    def service(self, api_name, api_version="v1"):
        if api_name not in self.services:
            self.services[api_name] = get_service(
                service_account_file=self.data["service_account_file"],
                oauth_file=self.data["oauth_file"],
                scope=["https://www.googleapis.com/auth/cloud-platform"],
                api_name=api_name,
                api_version=api_version,
            )
        return self.services[api_name]

    def get_compute(self):
        return self.service("compute", "v1")

    def get_zones(self, **zone_filter):
        zones = []
        for zone in self.get_compute().zones().list(
                project=self.data["project"]).execute()["items"]:
            is_ok = 1
            for k, v in zone_filter.items():
                if zone[k] != v:
                    is_ok = 0
                    continue
            if is_ok == 1:
                zones.append(zone["name"])
        return zones

    def update_instances(self):
        self.instances = {x["name"]: x for x in
                          self.get_compute().instances().list(
                              project=self.data["project"],
                              zone=self.data["zone"]).execute()["items"]}

    def get_instances(self, **instance_filter):
        self.update_instances()
        instances = []
        for instance, info in self.instances.items():
            is_ok = 1
            for k, v in instance_filter.items():
                if info[k] != v:
                    is_ok = 0
                    continue
            if is_ok == 1:
                instances.append(instance)
        return instances

    def check_instance(self, instance, status="RUNNING", n_wait=100,
                       wait_time=10):
        if n_wait <= 0:
            return True
        wait = n_wait
        while True:
            self.update_instances()
            if status == "DELETED":
                if instance not in self.instances:
                    return True
            elif status == "INSERTED":
                if instance in self.instances:
                    return True
            else:
                if instance not in self.instances:
                    continue
                if self.instances[instance]["status"] == status:
                    return True
            wait = wait - 1
            if wait <= 0:
                break
            sleep(wait_time)
        return False

    def start_instance(self, instance, n_wait=100, wait_time=10):
        if not self.check_instance(instance, "TERMINATED", 1, 1):
            self.logger.warning("%s is not TERMINATED status (status=%s)" %
                           (instance, self.instances[instance]["status"]))
            return False
        self.get_compute().instances().start(project=self.data["project"],
                                             zone=self.data["zone"],
                                             instance=instance).execute()
        return self.check_instance(instance, "RUNNING", n_wait, wait_time)

    def stop_instance(self, instance, n_wait=100, wait_time=10):
        if not self.check_instance(instance, "RUNNING", 1, 1):
            self.logger.warning("%s is not RUNNING status (status=%s)" %
                           (instance, self.instances[instance]["status"]))
            return False
        self.get_compute().instances().stop(project=self.data["project"],
                                            zone=self.data["zone"],
                                            instance=instance).execute()
        return self.check_instance(instance, "TERMINATED", n_wait, wait_time)

    def get_source_disk_image(self, family, project=""):
        if project == "":
            project = self.data["project"]
        image_response = self.get_compute().images().getFromFamily(
            project=project, family=family).execute()
        return image_response['selfLink']

    def insert_instance(self, instance, n_wait=100, wait_time=10, option={}):
        if self.check_instance(instance, "INSERTED", 1, 1):
            self.logger.warning("%s already exists" % instance)
            return False
        opt = deepcopy(option)
        if "name" not in opt:
            opt["name"] = instance
        if not opt["machineType"].startswith("zones"):
            opt["machineType"] = "zones/%s/machineTypes/%s" % (
                self.data["zone"], opt["machineType"])
        if "family" in opt:
            if "project" in opt:
                project = opt["project"]
            else:
                project = self.data["project"]
            source_disk_image = self.get_source_disk_image(opt["family"],
                                                           project)
            del opt["family"]
            if "disks" not in opt:
                opt["disks"] = [{}]
                opt["disks"][0] = {
                    "boot": True,
                    "autoDelete": True,
                }
            if "initializeParams" not in opt["disks"][0]:
                opt["disks"][0]["initializeParams"] = {}
            opt["disks"][0]["initializeParams"]["sourceImage"] =\
                source_disk_image
        if "networkInterfaces" not in opt:
            opt["networkInterfaces"] = [{
                "network": "global/networks/default",
                "accessConfigs": [
                    {"type": "ONE_TO_ONE_NAT", "name": "External NAT"}
                ]
            }]
        if "disks" not in opt:
            opt["networkInterfaces"] = [{
                "network": "global/networks/default",
                "accessConfigs": [
                    {"type": "ONE_TO_ONE_NAT", "name": "External NAT"}
                ]
            }]
        self.get_compute().instances().insert(project=self.data["project"],
                                              zone=self.data["zone"],
                                              body=opt).execute()
        if opt["disks"][0]["boot"]:
            return self.check_instance(instance, "RUNNING", n_wait, wait_time)
        else:
            return self.check_instance(instance, "INSERTED", n_wait, wait_time)

    def create_instance(self, instance, n_wait=100, wait_time=10, option={}):
        return self.insert_instance(instance, n_wait, wait_time, option)

    def delete_instance(self, instance, n_wait=100, wait_time=10):
        if self.check_instance(instance, "DELETED", 1, 1):
            self.logger.warning("%s does not exist)" % instance)
            return False
        self.get_compute().instances().delete(
            project=self.data["project"],
            zone=self.data["zone"],
            instance=instance,
        ).execute()
        return self.check_instance(instance, "DELETED", n_wait, wait_time)

    def get_storage(self):
        return self.service("storage", "v1")

    def is_bucket(self):
        storage = self.get_storage()
        bucket_list = [x["name"] for x in storage.buckets().list(
            project=self.data["project"]).execute()["items"]]
        return True if self.data["bucket"] in bucket_list else False

    def delete_bucket(self):
        storage = self.get_storage()
        if not self.is_bucket():
            return
        storage.buckets().delete(bucket=self.data["bucket"]).execute()

    def create_bucket(self):
        storage = self.get_storage()
        if self.is_bucket():
            return
        body = {"name": self.data["bucket"],
                "sotrageClass": self.data["storageClass"],
                "location": self.data["location"],
                }
        return storage.buckets().insert(project=self.data["project"],
                                        body=body).execute()

    def upload_file(self, file_name):
        storage = self.get_storage()
        self.create_bucket()
        with open(expand(file_name), 'rb') as f:
            response = storage.objects().insert(
                bucket=self.data["bucket"],
                media_body=googleapiclient.http.MediaIoBaseUpload(
                    f, 'application/octet-stream'),
                name=os.path.basename(file_name)).execute()
        return response

    def delete_file(self, file_name):
        storage = self.get_storage()
        return storage.objects().delete(
            bucket=self.data["bucket"], object=file_name).execute()
