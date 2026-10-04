# #4856 — Assertion failed: table.sub_tables.is_empty() when decorator class takes a lambda argument.

Class decorators are scanned before entering the class scope, matching code-generation order and keeping nested symbol tables aligned. The original source now compiles without the reported `table.sub_tables.is_empty()` panic.

Original issue: [https://github.com/RustPython/RustPython/issues/4856](https://github.com/RustPython/RustPython/issues/4856)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 4856
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
source = 'import unittest\nfrom unittest import mock\n\nclass MockedA(BaseFTests):\n    pass\n\n@mock.patch("", lambda: 3)\nclass MockedB(MockedA):\n    def _asserts(self, val):\n        pass\n'
compile(source, "repros/4856/issue-4856-case-01/source-01.txt", "exec")
print("compile_success")
```

The original source is compiled as a string. This directly exercises the reported compiler panic.

## Recorded comparison

- Historical result: Compiler panic: table.sub_tables.is_empty().
- Current result: compile_success (exit 0).
- Historical revision: [c7faae9b22ce31a3ba1f2cc1cd3ad759b54ce100](https://github.com/RustPython/RustPython/commit/c7faae9b22ce31a3ba1f2cc1cd3ad759b54ce100).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: the reported RustPython v0.2.0 release tag.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #8138](https://github.com/RustPython/RustPython/pull/8138): correct class-decorator scope scanning order.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
