from gcpm import __version__
from gcpm import core


def test_version():
    assert __version__ == '0.1.0'


def test_zones():
    g = core.Gcpm(project="grid-test-204503",
                  service_account_file="~/service_account.json")
    compute = g.get_compute()
    print(compute.zones().list(project=g.project).execute())
    assert True


def test_instances():
    g = core.Gcpm(project="grid-test-204503",
                  zone="asia-northeast1-b",
                  service_account_file="~/service_account.json")
    compute = g.get_compute()
    print(compute.instances().list(project=g.project, zone=g.zone).execute())
    assert True
