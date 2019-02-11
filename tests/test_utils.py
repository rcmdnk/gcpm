import os
from gcpm import utils


def test_expand():
    assert utils.expand("~/test") == utils.expand("$HOME/test")


def test_proc():
    (ret, stdout, stderr) = utils.proc(["pwd"])
    assert ret == 0
    assert stdout.strip() == os.getcwd()


def test_make_startup_script():
    script = utils.make_startup_script(
        core=8, mem=2560, swap=2560, disk=150, image="test-image",
        preemptible=1, admin="admin", head="head-node", port=1234,
        domain="example.com", owner="owner", bucket="test-bucket",
        off_timer=600)
    assert script.startswith("#!/usr")


def test_make_shutdown_script():
    script = utils.make_shutdown_script(
        core=8, mem=2560, swap=2560, disk=150, image="test-image",
        preemptible=1)
    assert script.startswith("#!/usr")
