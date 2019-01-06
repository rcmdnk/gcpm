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

    def is_bucket(self):
        return True if self.bucket in self.get_buckets() else False

    def get_buckets(self):
        bucket_list = [x["name"] for x in self.storage().buckets().list(
            project=self.project).execute()["items"]]
        return bucket_list

    def delete_bucket(self):
        if not self.is_bucket():
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

    def upload_file(self, file_name):
        self.create_bucket()
        with open(expand(file_name), 'rb') as f:
            response = self.storage().objects().insert(
                bucket=self.bucket,
                media_body=googleapiclient.http.MediaIoBaseUpload(
                    f, 'application/octet-stream'),
                name=os.path.basename(file_name)).execute()
        return response

    def delete_file(self, file_name):
        return self.storage().objects().delete(
            bucket=self.bucket, object=file_name).execute()
