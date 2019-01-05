from __future__ import print_function
import pytest
from gcpm import __version__

__TEST_INSTANCE__ = "gcpm-test-instance"


@pytest.mark.version
def test_version():
    assert __version__ == '0.1.0'


@pytest.mark.config
def test_show_config(default_gcpm):
    default_gcpm.show_config()
    assert True


@pytest.mark.compute
def test_zones(default_gcpm):
    zones = default_gcpm.get_zones()
    print(zones)
    assert "asia-northeast1-b" in zones


@pytest.mark.parametrize(
    "kw", [{}, {"status": "RUNNING"}])
@pytest.mark.compute
def test_instances(default_gcpm, kw):
    instances = default_gcpm.get_instances(**kw)
    print(instances)
    assert type(instances) == list


# option={"machineType": "custom-2-5120"}
# option={"machineType": "n1-standard-1"}
@pytest.mark.compute
def test_create(default_gcpm):
    assert default_gcpm.create_instance(
        instance=__TEST_INSTANCE__,
        option={
            "machineType": "custom-2-5120",
            "family": "centos-7",
            "project": "centos-cloud",
        }
    )


@pytest.mark.compute
def test_stop(default_gcpm):
    assert default_gcpm.stop_instance(__TEST_INSTANCE__)


@pytest.mark.compute
def test_start(default_gcpm):
    assert default_gcpm.start_instance(__TEST_INSTANCE__)


@pytest.mark.compute
def test_delete(default_gcpm):
    assert default_gcpm.delete_instance(__TEST_INSTANCE__)


@pytest.mark.storage
def test_storage(default_gcpm):
    storage = default_gcpm.get_storage()
    buckets = storage.buckets().list(
        project=default_gcpm.data["project"]).execute()
    print(buckets)
    assert "items" in buckets


@pytest.mark.storage
def test_create_bucket(default_gcpm):
    assert default_gcpm.create_bucket()["kind"] == "storage#bucket"


@pytest.mark.storage
def test_upload_file(default_gcpm):
    assert default_gcpm.upload_file("~/.bashrc")["kind"] == "storage#object"


@pytest.mark.storage
def test_delete_file(default_gcpm):
    assert default_gcpm.delete_file(".bashrc") == ""


@pytest.mark.storage
def test_delete_bucket(default_gcpm):
    assert default_gcpm.delete_bucket() is None
