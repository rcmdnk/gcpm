# -*- coding: utf-8 -*-

"""
    Module to mange Google Cloud Storage.
"""


import os
import logging
import googleapiclient
from .service import get_storage
from .utils import expand


class Gcs(object):

    def __init__(self, oauth_file="", service_account_file="", project="",
                 storageClass="", location="", bucket=""):
        self.oauth_file = oauth_file
        self.service_account_file = service_account_file
        self.project = project
        self.storageClass = storageClass
        self.location = location
        self.bucket = bucket
        self.storage_service = None
        self.logger = logging.getLogger(__name__)

    def storage(self):
        if self.storage_service is None:
            self.storage_service = get_storage(
                service_account_file=self.service_account_file,
                oauth_file=self.oauth_file,
            )
        return self.storage_service

    def get_buckets(self):
        buckets = self.storage().buckets().list(project=self.project).execute()
        if "items" not in buckets:
            return []
        return [x["name"] for x in buckets]

    def is_bucket(self, bucket):
        return True if bucket in self.get_buckets() else False

    def delete_bucket(self):
        if not self.is_bucket(self.bucket):
            return
        self.storage().buckets().delete(bucket=self.bucket).execute()

    def create_bucket(self):
        if self.is_bucket():
            return
        body = {"name": self.bucket,
                "sotrageClass": self.storageClass,
                "location": self.location,
                }
        return self.storage().buckets().insert(project=self.project,
                                               body=body).execute()

    def get_files(self):
        files = self.storage().objects().list(bucket=self.bucket).execute()
        if "items" not in files:
            return []
        return [x["name"] for x in files]

    def is_file(self, filename):
        return True if filename in self.get_files() else False

    def upload_file(self, path, filename="", is_warn_exist=False):
        self.create_bucket()
        if filename == ""
            filename = os.path.basename(path)
        if self.is_file(filename):
            if is_warn_exist:
                self.logger.warning("%s already exists on %s"
                                    % (filename, self.bucket)
            return None
        with open(expand(path), 'rb') as f:
            response = self.storage().objects().insert(
                bucket=self.bucket,
                media_body=googleapiclient.http.MediaIoBaseUpload(
                    f, 'application/octet-stream'),
                name=filename).execute()
        return response

    def delete_file(self, filename):
        return self.storage().objects().delete(
            bucket=self.bucket, object=filename).execute()
