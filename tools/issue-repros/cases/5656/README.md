# #5656 — Not properly checking for invalid escape seqeunce \X

Original issue: [#5656](https://github.com/RustPython/RustPython/issues/5656)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'assert b"omkmok\Xaa" == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])'
```

## Before and after

- **Before — [c3ed002b1204](https://github.com/RustPython/RustPython/commit/c3ed002b1204d9ff156b5192b634a4056101b255) (nearest pre-issue main revision; approximate baseline):** The assertion passes without the required invalid-escape warning.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** The assertion passes and stderr contains SyntaxWarning for \X.

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

Compilation detects invalid escapes in bytes literals and emits the corresponding warning. The original bytes assertion still passes and now emits the missing `SyntaxWarning` for `\X`, satisfying the report.

[PR #7164](https://github.com/RustPython/RustPython/pull/7164): invalid string and bytes escape warnings.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
