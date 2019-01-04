# -*- coding: utf-8 -*-

"""
    Core module to provides gcpm functions.
"""


from __future__ import print_function
import os
from .service import get_service
from .utils import expand
import ruamel.yaml


class Gcpm(object):
    """HTCondor pool manager for Google Cloud Platform."""

    def __init__(self, config="~/.config/gcpm/gcpm.yaml"):
        self.config = expand(config)
        self.services = {}
        self.data = {
            "oauth_file": "~/.config/gcpm/oauth",
            "service_account_file": "",
            "project": "",
            "zone": "",
            "storageClass": "REGIONAL",
            "location": "",
        }
        self.read_config()

    def read_config(self):
        if not os.path.isfile(self.config):
            print(self.config + " does not exist")
            return
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

    def show_config(self):
        print(self.data)

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

    def get_storage(self):
        return self.service("storage", "v1")

    def bucket_name(self, bucket):
        if bucket == "":
            raise ValueError("bucket is emptry")
        if bucket.startswith("gs://"):
            bucket = bucket.replace("gs://", "")
        return bucket

    def is_bucket(self, bucket):
        storage = self.get_storage()
        bucket = self.bucket(bucket)
        bucket_list = [x["name"] for x in storage.buckets().list(
            project=self.data["project"]).execute()["items"]]
        return True if bucket in bucket_list else False

    def delete_bucket(self, bucket):
        storage = self.get_storage()
        bucket = self.bucket_name(bucket)
        if not self.is_bucket(bucket):
            return
        storage.buckets().delete(bucket=bucket).execute()

    def create_bucket(self, bucket):
        storage = self.get_storage()
        bucket = self.bucket_name(bucket)
        if self.is_bucket(bucket):
            return
        body = {"name": bucket,
                "sotrageClass": self.data["storageClass"],
                "location": self.data["location"],
                }
        storage.buckets().insert(project=self.data["project"],
                                 body=body).execute()
