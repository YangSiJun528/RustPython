# #6429 — `sysconfig.get_config_var('Py_GIL_DISABLED')` returns `None`

Build-time configuration now defines `Py_GIL_DISABLED` as `1`. On POSIX/macOS, `sysconfig.get_config_var("Py_GIL_DISABLED")` returns `1`, resolving the reported missing configuration value.

Original issue: [https://github.com/RustPython/RustPython/issues/6429](https://github.com/RustPython/RustPython/issues/6429)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 6429
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
import sysconfig

print(repr(sysconfig.get_config_var("Py_GIL_DISABLED")), flush=True)
```

The missing import is supplied and the queried value is printed.

## Recorded comparison

- Historical result: Py_GIL_DISABLED is None.
- Current result: Py_GIL_DISABLED is 1 on the tested POSIX build.
- Historical revision: [e227956a58f0f072f8be177264e0fdc1b9280e8a](https://github.com/RustPython/RustPython/commit/e227956a58f0f072f8be177264e0fdc1b9280e8a).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose `Py_GIL_DISABLED` in build-time variables.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
