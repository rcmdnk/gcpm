from __future__ import print_function
import pytest


@pytest.mark.storage
def test_create_bucket(default_gcpm):
    assert default_gcpm.get_gcs().create_bucket()["kind"] == "storage#bucket"


@pytest.mark.storage
def test_storage(default_gcpm):
    assert default_gcpm.data["bucket"] in default_gcpm.get_gcs().get_buckets()


@pytest.mark.storage
def test_upload_file(default_gcpm):
    assert default_gcpm.get_gcs().upload_file("~/.bashrc")["kind"]\
        == "storage#object"


@pytest.mark.storage
def test_delete_file(default_gcpm):
    assert default_gcpm.get_gcs().delete_file(".bashrc") == ""


@pytest.mark.storage
def test_delete_bucket(default_gcpm):
    assert default_gcpm.get_gcs().delete_bucket() is None
