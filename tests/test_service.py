from gcpm import service


def test_service_from_oauth():
    service.get_service()
    assert True


def test_service_from_service_account():
    service.get_service(service_account_file="~/service_account.json")
    assert True
