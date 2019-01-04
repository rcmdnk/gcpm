# -*- coding: utf-8 -*-

"""
    Core module to provides gcpm functions.
"""


from __future__ import print_function
import os
from .service import get_service
from .utils import expand
import ruamel.yaml
import googleapiclient


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
            "bucket": "",
            "storageClass": "REGIONAL",
            "location": "",
        }
        self.read_config()

    def bucket_name(self, bucket):
        if bucket == "":
            raise ValueError("bucket is emptry")
        if bucket.startswith("gs://"):
            bucket = bucket.replace("gs://", "")
        return bucket

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
        if self.data["bucket"] == "":
            self.data["bucket"] = self.data["project"] + "_" + "gcpm_bucket"
        self.data["bucket"] = self.bucket_name(self.data["bucket"])

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
        storage.buckets().insert(project=self.data["project"],
                                 body=body).execute()

    def upload_file(self, file_name):
        storage = self.get_storage()
        self.create_bucket()
        with open(expand(file_name), 'rb') as f:
            storage.objects().insert(
                bucket=self.data["bucket"],
                media_body=googleapiclient.http.MediaIoBaseUpload(
                    f, 'application/octet-stream'),
                name=os.path.basename(file_name)).execute()

    def delete_file(self, file_name):
        storage = self.get_storage()
        storage.objects().delete(
            bucket=self.data["bucket"], object=file_name).execute()
