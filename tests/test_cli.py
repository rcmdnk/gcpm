from __future__ import print_function
import sys
from gcpm.cli import cli


__ORIG_ARGV__ = sys.argv


def test_show_config():
    sys.argv = ["gcpm", "show-config", "--config", "./tests/data/gcpm.yml"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True


def test_run():
    sys.argv = ["gcpm", "run", "--config", "./tests/data/gcpm.yml"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True


def test_set_pool_password():
    sys.argv = ["gcpm" "set-pool-password", "--config",
                "./tests/data/gcpm.yml"]
    cli()
    sys.argv = __ORIG_ARGV__
    assert True
