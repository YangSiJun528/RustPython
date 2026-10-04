# #4762 — cformat star asterisk should behave differently when given negative sign

Original issue: [#4762](https://github.com/RustPython/RustPython/issues/4762)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'assert "%*s" % (-5, "abc") == "abc  "'
```

## Before and after

- **Before — [c36e3612e7dd](https://github.com/RustPython/RustPython/commit/c36e3612e7dd1c7abd9fc7b76b912372bd26afbf) (nearest pre-issue main revision; approximate baseline):** The negative-width assertion raises AssertionError.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** The assertion passes; two trailing spaces are retained.

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

Negative dynamic widths now select left alignment. The original `'%*s' % (-5, 'abc') == 'abc  '` assertion passes, including the two trailing spaces.

[PR #4766](https://github.com/RustPython/RustPython/pull/4766): preserve left alignment for negative dynamic widths.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
