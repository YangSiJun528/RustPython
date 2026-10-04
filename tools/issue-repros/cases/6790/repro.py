import unittest

from test import support


def dummy():
    pass


selected = support.requires_lzma()(dummy)
print("skip", getattr(selected, "__unittest_skip__", False))
print("reason", getattr(selected, "__unittest_skip_why__", None))
try:
    selected()
    print("invoked", "success")
except unittest.SkipTest as exc:
    print("invoked", "SkipTest")
    print("skip_message", str(exc))
