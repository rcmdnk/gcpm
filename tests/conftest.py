import pytest
from gcpm import core


@pytest.fixture(scope="session")
def default_gcpm():
    print('prepare gcpm')
    return core.Gcpm("./tests/data/gcpm.yaml")


@pytest.fixture(scope="session")
def oauth_gcpm():
    print('prepare gcpm')
    return core.Gcpm("./tests/data/gcpm_oauth.yaml")
