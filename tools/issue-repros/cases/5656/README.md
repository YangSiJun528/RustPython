# #5656 — Not properly checking for invalid escape seqeunce \X

Compilation detects invalid escapes in bytes literals and emits the corresponding warning. The original bytes assertion still passes and now emits the missing `SyntaxWarning` for `\X`, satisfying the report.

Original issue: [https://github.com/RustPython/RustPython/issues/5656](https://github.com/RustPython/RustPython/issues/5656)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 5656
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
assert b"omkmok\Xaa" == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])
```

The original executable input is retained.

## Recorded comparison

- Historical result: The assertion passes without the required invalid-escape warning.
- Current result: The assertion passes and stderr contains SyntaxWarning for \X.
- Historical revision: [c3ed002b1204d9ff156b5192b634a4056101b255](https://github.com/RustPython/RustPython/commit/c3ed002b1204d9ff156b5192b634a4056101b255).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #7164](https://github.com/RustPython/RustPython/pull/7164): invalid string and bytes escape warnings.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
