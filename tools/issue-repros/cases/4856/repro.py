source = """\
import unittest
from unittest import mock

class MockedA(BaseFTests):
    pass

@mock.patch("", lambda: 3)
class MockedB(MockedA):
    def _asserts(self, val):
        pass
"""
compile(source, "repros/4856/issue-4856-case-01/source-01.txt", "exec")
print("compile_success")
