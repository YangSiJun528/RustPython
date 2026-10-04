# #4908 — ast.parse() fails to handle "A[1:2, *l]" after it is parsed and unparsed.

Original issue: [#4908](https://github.com/RustPython/RustPython/issues/4908)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
import ast

code_1 = "A[1:2, *l]"
tree_1 = ast.parse(code_1)  # work normally

code_2 = ast.unparse(tree_1)
print(code_2)  # str "A[1:2, *l]"
tree_2 = ast.parse(code_2)  # fail
'
```

## Before and after

- **Before — [471ec268737c](https://github.com/RustPython/RustPython/commit/471ec268737c789ba861a6f7762128fc2ed21323) (revision identified in the report):** Unparses to A[(1:2, *l)]; reparsing raises SyntaxError.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** A[1:2, *l] unparses and reparses successfully.

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

The unparser handles nonempty subscript tuples containing starred elements without introducing invalid parentheses around slices. `A[1:2, *l]` now unparses and reparses successfully, resolving the reported invalid-syntax output.

[PR #5121](https://github.com/RustPython/RustPython/pull/5121): correct subscript-tuple unparsing.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
