# AST round trip for a starred subscript (#4908)

[Original issue](https://github.com/RustPython/RustPython/issues/4908). **Resolved in the reported scope.** The original starred subscript unparses to valid syntax and reparses; extended combinations preserve AST structure.

## Environment

- Source and standard library: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Verified October 5, 2026 on macOS 26.5.2 ARM64.
- RustPython: 0.6.1, Python 3.14.0.alpha; native ARM64.
- Comparison: CPython 3.14.6 ARM64.

Use absolute paths for the variables below:

- `RP`: the RustPython executable for this commit.
- `CP`: the CPython 3.14.6 executable.
- `SRC`: the source directory at this commit, including its matching `Lib`.
- `CASE`: the directory containing the files shown below.

Shell variables replace recorded absolute paths. Export them so the Python inputs can use them:

```sh
export RP CP SRC CASE
unset PYTHONPATH PYTHONHOME PYTHONWARNINGS PYTHONSTARTUP
export PYTHONDONTWRITEBYTECODE=1
```

## Reproducer

Save as `4908-original.py`.

```python
import ast

code_1 = "A[1:2, *l]"
tree_1 = ast.parse(code_1)
code_2 = ast.unparse(tree_1)
print(code_2)
tree_2 = ast.parse(code_2)
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/4908-original.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/4908-original.py"
```

## Results

**Expected:** Unparsing A[1:2, *l] must yield a valid subscript expression.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
A[1:2, *l]
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`471ec268737c`](https://github.com/RustPython/RustPython/commit/471ec268737c789ba861a6f7762128fc2ed21323); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:**

```text
A[(1:2, *l)]
```

**stderr:**

```text
Traceback (most recent call last):
  File "<survey>/repros/4908/issue-4908-case-01/source-01.txt", line 7, in <module>
    tree_2 = ast.parse(code_2)  #fail
  File "<checkout>/pylib/Lib/ast.py", line 51, in parse
    _feature_version=feature_version)
SyntaxError: invalid syntax. Got unexpected token ':' at line 1 column 5
A[(1:2, *l)]
    ^
```

## Related change and scope

[PR #5121](https://github.com/RustPython/RustPython/pull/5121): valid subscript-tuple unparsing.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-a/4908-original-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-a/4908-original-rp.json).
- [Executed source](../../evidence/initial16/agent-a/4908-original.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/4908/evidence/metadata.json).

AI assistance: OpenAI Codex.
