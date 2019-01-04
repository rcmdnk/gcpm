import pytest
from gcpm import service


@pytest.mark.parametrize(
    "kw", [{}, {"service_account_file": "tests/data/service_account.json"}])
def test_service(kw):
    service.get_service(**kw)
    assert True
