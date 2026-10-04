# #6429 — `sysconfig.get_config_var('Py_GIL_DISABLED')` returns `None`

Original issue: [#6429](https://github.com/RustPython/RustPython/issues/6429)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'import sysconfig; print(repr(sysconfig.get_config_var("Py_GIL_DISABLED")), flush=True)'
```

## Before and after

- **Before — [e227956a58f0](https://github.com/RustPython/RustPython/commit/e227956a58f0f072f8be177264e0fdc1b9280e8a) (nearest pre-issue main revision; approximate baseline):** Py_GIL_DISABLED is None.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** Py_GIL_DISABLED is 1 on the tested POSIX build.

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

Build-time configuration now defines `Py_GIL_DISABLED` as `1`. On POSIX/macOS, `sysconfig.get_config_var("Py_GIL_DISABLED")` returns `1`, resolving the reported missing configuration value.

[PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose `Py_GIL_DISABLED` in build-time variables.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
