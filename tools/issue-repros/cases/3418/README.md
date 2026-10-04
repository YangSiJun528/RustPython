# #3418 — Introduce `_collections.OrderedDict` type (a.k.a. `collections.OrderedDict`)

Original issue: [#3418](https://github.com/RustPython/RustPython/issues/3418)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'from _collections import OrderedDict'
```

## Before and after

- **Before — [40fd9c2683d7](https://github.com/RustPython/RustPython/commit/40fd9c2683d76adf2b9ed0d77c055e2d2514c27d) (nearest pre-issue main revision; approximate baseline):** ImportError importing OrderedDict from _collections.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** The import succeeds (exit 0).

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

A native `OrderedDict` is now exported from `_collections`. The requested `from _collections import OrderedDict` import succeeds, satisfying the reported missing-export issue.

[PR #8780](https://github.com/RustPython/RustPython/pull/8780): native `OrderedDict` implementation and export.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
