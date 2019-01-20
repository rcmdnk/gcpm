import os
import pytest
from gcpm import files


@pytest.mark.skip
def test_service():
    filename = "./gcpm.service"
    files.make_service(filename=filename)
    assert os.path.isfile(filename)
    files.rm_service(filename=filename)
    assert not os.path.isfile(filename)


def test_logrotate():
    filename = "./gcpm.conf"
    files.make_logrotate(filename=filename)
    assert os.path.isfile(filename)
    files.rm_logrotate(filename=filename)
    assert not os.path.isfile(filename)
