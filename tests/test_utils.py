import os
from gcpm import utils


def test_expand():
    assert utils.expand("~/test") == utils.expand("$HOME/test")


def test_proc():
    (ret, stdout, stderr) = utils.proc(["hostname"])
    assert ret == 0
    assert stdout == os.environ["HOSTNAME"]
