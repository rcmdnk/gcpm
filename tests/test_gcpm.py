from gcpm import __version__
from gcpm import core


def test_version():
    assert __version__ == '0.1.0'


def test_show_config():
    g = core.Gcpm()
    g.show_config()
    assert True


def test_zones():
    g = core.Gcpm()
    compute = g.get_compute()
    zones = compute.zones().list(project=g.data["project"]).execute()
    print(zones)
    assert zones["items"][0]["kind"] == "compute#zone"


def test_instances():
    g = core.Gcpm()
    compute = g.get_compute()
    instances = compute.instances().list(project=g.data["project"],
                                         zone=g.data["zone"]).execute()
    print(instances)
    assert "items" in instances


def test_storage():
    g = core.Gcpm()
    storage = g.get_storage()
    buckets = storage.buckets().list(project=g.data["project"]).execute()
    print(buckets)
    assert "items" in buckets


def test_create_bucket():
    g = core.Gcpm()
    g.create_bucket("my_gcpm_test_bucket")
    assert True


def test_delete_bucket():
    g = core.Gcpm()
    g.delete_bucket("my_gcpm_test_bucket")
    assert True
