# #4908 — ast.parse() fails to handle "A[1:2, *l]" after it is parsed and unparsed.

The unparser handles nonempty subscript tuples containing starred elements without introducing invalid parentheses around slices. `A[1:2, *l]` now unparses and reparses successfully, resolving the reported invalid-syntax output.

Original issue: [https://github.com/RustPython/RustPython/issues/4908](https://github.com/RustPython/RustPython/issues/4908)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 4908
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
import ast

code_1 = "A[1:2, *l]"
tree_1 = ast.parse(code_1)  # work normally

code_2 = ast.unparse(tree_1)
print(code_2)  # str "A[1:2, *l]"
tree_2 = ast.parse(code_2)  # fail
```

The original executable input is retained.

## Recorded comparison

- Historical result: Unparses to A[(1:2, *l)]; reparsing raises SyntaxError.
- Current result: A[1:2, *l] unparses and reparses successfully.
- Historical revision: [471ec268737c789ba861a6f7762128fc2ed21323](https://github.com/RustPython/RustPython/commit/471ec268737c789ba861a6f7762128fc2ed21323).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: a revision identified in the original report.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #5121](https://github.com/RustPython/RustPython/pull/5121): correct subscript-tuple unparsing.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
