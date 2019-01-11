from __future__ import print_function
import os
import sys
import shutil
import tempfile
import pytest
from gcpm.cli import cli


__ORIG_ARGV__ = sys.argv


def test_show_config():
    sys.argv = ["gcpm", "show-config", "--config", "./tests/data/gcpm.yml"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True


def test_help():
    sys.argv = ["gcpm", "help"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True


def test_version():
    sys.argv = ["gcpm", "version"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True


@pytest.mark.skip
def test_install():
    sys.argv = ["gcpm", "install"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True


@pytest.mark.skip
def test_uninstall():
    sys.argv = ["gcpm", "uninstall"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True


@pytest.mark.skip
def test_run():
    sys.argv = ["gcpm", "run", "--config", "./tests/data/gcpm.yml"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True


@pytest.mark.skip
def test_service():
    sys.argv = ["gcpm", "service", "--config", "./tests/data/gcpm.yml"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True


def test_set_pool_password(default_gcpm):
    directory = tempfile.mkdtemp()
    filename = directory + "/pool_password"
    with open(filename, "a"):
        os.utime(filename, None)

    sys.argv = ["gcpm", "set-pool-password", filename,
                "--config", "./tests/data/gcpm.yml"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True
    assert default_gcpm.get_gcs().delete_file("pool_password") == ""
    assert default_gcpm.get_gcs().delete_bucket() is None
    shutil.rmtree(directory)
