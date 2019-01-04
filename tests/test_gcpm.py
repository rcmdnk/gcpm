import pytest
from gcpm import __version__
from gcpm import core


@pytest.mark.version
def test_version():
    assert __version__ == '0.1.0'


@pytest.mark.config
def test_show_config():
    g = core.Gcpm()
    g.show_config()
    assert True


@pytest.mark.compute
def test_zones():
    g = core.Gcpm()
    compute = g.get_compute()
    zones = compute.zones().list(project=g.data["project"]).execute()
    print(zones)
    assert zones["items"][0]["kind"] == "compute#zone"


@pytest.mark.compute
def test_instances():
    g = core.Gcpm()
    compute = g.get_compute()
    instances = compute.instances().list(project=g.data["project"],
                                         zone=g.data["zone"]).execute()
    print(instances)
    assert "items" in instances


@pytest.mark.storage
def test_storage():
    g = core.Gcpm()
    storage = g.get_storage()
    buckets = storage.buckets().list(project=g.data["project"]).execute()
    print(buckets)
    assert "items" in buckets


@pytest.mark.storage
def test_create_bucket():
    g = core.Gcpm()
    g.create_bucket()
    assert True


@pytest.mark.storage
def test_upload_file():
    g = core.Gcpm()
    g.upload_file("~/.bashrc")
    assert True


@pytest.mark.storage
def test_delete_file():
    g = core.Gcpm()
    g.delete_file(".bashrc")
    assert True


@pytest.mark.storage
def test_delete_bucket():
    g = core.Gcpm()
    g.delete_bucket()
    assert True
