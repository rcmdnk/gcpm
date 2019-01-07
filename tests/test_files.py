import os
from gcpm import files


def test_startup_script():
    files.make_startup_script(filename="./startup_test.sh", core=8, mem=2560, disk=150,
                         image="test-image", preemptible=1, admin="admin",
                         head="head-node", port=1234, domain="example.com",
                         owner="owner", bucket="test-bucket", off_timer=600)
    assert os.path.isfile("./startup_test.sh")
    os.remove("./startup_8core.sh")


def test_shutdown_script():
    files.make_shutdown_script(filename="./shutdown_test.sh")
    assert os.path.isfile("./shutdown_test.sh")
    os.remove("./shutdown_8core.sh")
