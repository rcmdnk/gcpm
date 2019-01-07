from __future__ import print_function
import os
import tempfile
import pytest


@pytest.mark.storage
def test_create_bucket(default_gcpm):
    assert default_gcpm.get_gcs().create_bucket()["kind"] == "storage#bucket"


@pytest.mark.storage
def test_storage(default_gcpm):
    assert default_gcpm.data["bucket"] in default_gcpm.get_gcs().get_buckets()


@pytest.mark.storage
def test_upload_delete_file(default_gcpm):
    with tempfile.NamedTemporaryFile() as f:
        name = f.name
        assert default_gcpm.get_gcs().upload_file(name)["kind"]\
            == "storage#object"
        basename = os.path.basename(name)
        assert default_gcpm.get_gcs().delete_file(basename) == ""


@pytest.mark.storage
def test_delete_bucket(default_gcpm):
    assert default_gcpm.get_gcs().delete_bucket() is None
