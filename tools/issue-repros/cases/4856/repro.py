source = 'import unittest\nfrom unittest import mock\n\nclass MockedA(BaseFTests):\n    pass\n\n@mock.patch("", lambda: 3)\nclass MockedB(MockedA):\n    def _asserts(self, val):\n        pass\n'
compile(source, "repros/4856/issue-4856-case-01/source-01.txt", "exec")
print("compile_success")
