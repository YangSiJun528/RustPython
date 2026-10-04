# #4786 — Type name cannot contain surrogates

String literals preserve lone surrogates, and type-name validation rejects them. The original `type("A\udcdcB", (), {})` input now raises the expected `UnicodeEncodeError`, resolving the silent replacement-character behavior.

Original issue: [https://github.com/RustPython/RustPython/issues/4786](https://github.com/RustPython/RustPython/issues/4786)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 4786
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
print(repr(type("A\udcdcB", (), {})))
```

The transcript expression is wrapped in print(repr(...)) to expose a wrongly accepted type; the correct outcome is an uncaught UnicodeEncodeError.

## Recorded comparison

- Historical result: Creates a type whose name contains a replacement character.
- Current result: UnicodeEncodeError rejects the surrogate in the name (expected exit 1).
- Historical revision: [010640ccc8f74f56075df09a654352ae3d162d25](https://github.com/RustPython/RustPython/commit/010640ccc8f74f56075df09a654352ae3d162d25).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #5629](https://github.com/RustPython/RustPython/pull/5629): preserve surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
