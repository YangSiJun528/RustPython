# #8052 — `type(...).__name__` is `'EllipsisType'` instead of `'ellipsis'`

Original issue: [#8052](https://github.com/RustPython/RustPython/issues/8052)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'print(type(...).__name__); print(repr(type(...)))'
```

## Before and after

- **Before — [83fe92042112](https://github.com/RustPython/RustPython/commit/83fe92042112f9db89a70495b552ab433d77e751) (nearest pre-issue main revision; approximate baseline):** EllipsisType and <class 'EllipsisType'>.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** ellipsis and <class 'ellipsis'>, matching CPython.

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

The built-in type is now named `ellipsis`. The original query returns `ellipsis` and `<class 'ellipsis'>`, matching CPython and resolving both reported naming outputs.

[PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
