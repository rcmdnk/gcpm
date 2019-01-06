# -*- coding: utf-8 -*-

"""
    Module to mange Google Compute Engine.
"""


import logging
from copy import deepcopy
from time import sleep
from .service import get_compute


class Gce(object):

    def __init__(self, oauth_file="", service_account_file="", project="",
                 zone=""):
        self.oauth_file = oauth_file
        self.service_account_file = service_account_file
        self.project = project
        self.zone = zone
        self.instances = {}
        self.compute_service = None
        self.n_wait = 100
        self.wait_time = 10
        self.logger = logging.getLogger(__name__)

    def compute(self):
        if self.compute_service is None:
            self.compute_service = get_compute(
                service_account_file=self.service_account_file,
                oauth_file=self.oauth_file,
            )
        return self.compute_service

    def get_zones(self, **zone_filter):
        zones = []
        for zone in self.compute().zones().list(
                project=self.project).execute()["items"]:
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
                          self.compute().instances().list(
                              project=self.project,
                              zone=self.zone).execute()["items"]}

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

    def check_instance(self, instance, status="RUNNING", n_wait=-1,
                       wait_time=-1):
        if n_wait == -1:
            n_wait = self.n_wait
        if wait_time == -1:
            wait_time = self.wait_time
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

    def start_instance(self, instance, n_wait=-1, wait_time=-1):
        if not self.check_instance(instance, "TERMINATED", 1, 1):
            self.logger.warning("%s is not TERMINATED status (status=%s)" %
                                (instance, self.instances[instance]["status"]))
            return False
        self.compute().instances().start(project=self.project,
                                         zone=self.zone,
                                         instance=instance).execute()
        return self.check_instance(instance, "RUNNING", n_wait, wait_time)

    def stop_instance(self, instance, n_wait=-1, wait_time=-1):
        if not self.check_instance(instance, "RUNNING", 1, 1):
            self.logger.warning("%s is not RUNNING status (status=%s)" %
                                (instance, self.instances[instance]["status"]))
            return False
        self.compute().instances().stop(project=self.project,
                                        zone=self.zone,
                                        instance=instance).execute()
        return self.check_instance(instance, "TERMINATED", n_wait, wait_time)

    def get_source_disk_image(self, family, project=""):
        if project == "":
            project = self.project
        image_response = self.compute().images().getFromFamily(
            project=project, family=family).execute()
        return image_response['selfLink']

    def insert_instance(self, instance, n_wait=-1, wait_time=-1, option={}):
        if self.check_instance(instance, "INSERTED", 1, 1):
            self.logger.warning("%s already exists" % instance)
            return False
        opt = deepcopy(option)
        if "name" not in opt:
            opt["name"] = instance
        if not opt["machineType"].startswith("zones"):
            opt["machineType"] = "zones/%s/machineTypes/%s" % (
                self.zone, opt["machineType"])
        if "family" in opt:
            if "project" in opt:
                project = opt["project"]
            else:
                project = self.project
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
        self.compute().instances().insert(project=self.project,
                                          zone=self.zone,
                                          body=opt).execute()
        if opt["disks"][0]["boot"]:
            return self.check_instance(instance, "RUNNING", n_wait, wait_time)
        else:
            return self.check_instance(instance, "INSERTED", n_wait, wait_time)

    def create_instance(self, instance, n_wait=-1, wait_time=-1, option={}):
        return self.insert_instance(instance, n_wait, wait_time, option)

    def delete_instance(self, instance, n_wait=-1, wait_time=-1):
        if self.check_instance(instance, "DELETED", 1, 1):
            self.logger.warning("%s does not exist)" % instance)
            return False
        self.compute().instances().delete(
            project=self.project,
            zone=self.zone,
            instance=instance,
        ).execute()
        return self.check_instance(instance, "DELETED", n_wait, wait_time)
