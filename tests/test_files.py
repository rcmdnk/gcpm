import os
from gcpm import files


def test_startup_script():
    filename = "./startup-test.sh"
    files.make_startup_script(filename=filename, core=8, mem=2560, disk=150,
                              image="test-image", preemptible=1, admin="admin",
                              head="head-node", port=1234,
                              domain="example.com", owner="owner",
                              bucket="test-bucket", off_timer=600)
    assert os.path.isfile(filename)
    os.remove(filename)


def test_shutdown_script():
    filename = "./shutdown-test.sh"
    files.make_shutdown_script(filename=filename)
    assert os.path.isfile(filename)
    os.remove(filename)


def test_service():
    filename = "./gcpm.service"
    files.make_service(filename=filename)
    assert os.path.isfile(filename)
    files.rm_service(filename=filename)


def test_logrotate():
    filename = "./gcpm.conf"
    files.make_logrotate(filename=filename)
    assert os.path.isfile(filename)
    files.rm_logrotate(filename=filename)
