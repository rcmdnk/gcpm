from __future__ import print_function
import pytest
from gcpm import __version__

__TEST_INSTANCE__ = "gcpm-test-instance"


@pytest.mark.version
def test_version():
    assert __version__ == '0.3.1'


@pytest.mark.config
def test_show_config(default_gcpm):
    default_gcpm.show_config()
    assert True
