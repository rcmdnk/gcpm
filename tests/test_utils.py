from gcpm import utils


def test_expand():
    assert utils.expand("~/test") == utils.expand("$HOME/test")
