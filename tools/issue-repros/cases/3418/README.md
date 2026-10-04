# #3418 — Introduce `_collections.OrderedDict` type (a.k.a. `collections.OrderedDict`)

A native `OrderedDict` is now exported from `_collections`. The requested `from _collections import OrderedDict` import succeeds, satisfying the reported missing-export issue.

Original issue: [https://github.com/RustPython/RustPython/issues/3418](https://github.com/RustPython/RustPython/issues/3418)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 3418
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
from _collections import OrderedDict
```

The original executable input is retained.

## Recorded comparison

- Historical result: ImportError importing OrderedDict from _collections.
- Current result: The import succeeds (exit 0).
- Historical revision: [40fd9c2683d76adf2b9ed0d77c055e2d2514c27d](https://github.com/RustPython/RustPython/commit/40fd9c2683d76adf2b9ed0d77c055e2d2514c27d).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #8780](https://github.com/RustPython/RustPython/pull/8780): native `OrderedDict` implementation and export.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
