from gcpm import service


def test_service():
    service.service("~/service_account.json")
    assert True
