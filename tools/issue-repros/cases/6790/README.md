# #6790 — Support xz

The unconditional `lzma = None` override was removed from `requires_lzma`. With the module available, `requires_lzma()(dummy)` now invokes the function successfully; the requested removal of the forced skip is complete.

Original issue: [https://github.com/RustPython/RustPython/issues/6790](https://github.com/RustPython/RustPython/issues/6790)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 6790
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
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
```

A derived probe applies requires_lzma()(dummy), then invokes the wrapped function and records whether it skips.

Use the matching RustPython `Lib` tree, including `test.support`, with lzma available.

## Recorded comparison

- Historical result: The decorated function raises SkipTest: requires lzma.
- Current result: skip False; reason None; invoked success.
- Historical revision: [ed785e3d868966e2a5f7478632cabd5a630e6934](https://github.com/RustPython/RustPython/commit/ed785e3d868966e2a5f7478632cabd5a630e6934).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: the source revision linked by the original report.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #7896](https://github.com/RustPython/RustPython/pull/7896): remove the unconditional lzma skip override.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
