# AST round trip for a starred subscript (#4908)

Original issue: [#4908](https://github.com/RustPython/RustPython/issues/4908)

**Verified closure candidate:** The original starred subscript unparses to valid syntax and reparses; extended combinations preserve AST structure.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [4908-original.py](../../evidence/initial16/agent-a/4908-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
import ast

code_1 = "A[1:2, *l]"
tree_1 = ast.parse(code_1)
code_2 = ast.unparse(tree_1)
print(code_2)
tree_2 = ast.parse(code_2)
```

## Expected and observed results

**Expected:** Unparsing A[1:2, *l] must yield a valid subscript expression.

**Observed:** The original starred subscript unparses to valid syntax and reparses; extended combinations preserve AST structure.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
A[1:2, *l]
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
A[1:2, *l]
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:**

```text
A[(1:2, *l)]
```

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
Traceback (most recent call last):
  File "<survey>/repros/4908/issue-4908-case-01/source-01.txt", line 7, in <module>
    tree_2 = ast.parse(code_2)  #fail
  File "<checkout>/pylib/Lib/ast.py", line 51, in parse
    _feature_version=feature_version)
SyntaxError: invalid syntax. Got unexpected token ':' at line 1 column 5
A[(1:2, *l)]
    ^
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B \
  '<initial16-audit>/agent-a/4908-original.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<initial16-audit>/agent-a/4908-original.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

The original starred subscript unparses to valid syntax and reparses; extended combinations preserve AST structure.

[PR #5121](https://github.com/RustPython/RustPython/pull/5121): valid subscript-tuple unparsing.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The claim covers the reported syntax and selected round-trip variants.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4908/evidence/metadata.json).
- Historical baseline: [`471ec268737c`](https://github.com/RustPython/RustPython/commit/471ec268737c789ba861a6f7762128fc2ed21323), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/4908/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/4908/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[4908-boundaries-cp](../../evidence/initial16/agent-a/4908-boundaries-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4908-boundaries-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4908-boundaries-cp.stderr).
- **[4908-boundaries-rp](../../evidence/initial16/agent-a/4908-boundaries-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4908-boundaries-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4908-boundaries-rp.stderr).
- **[4908-original-cp](../../evidence/initial16/agent-a/4908-original-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4908-original-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4908-original-cp.stderr).
- **[4908-original-rp](../../evidence/initial16/agent-a/4908-original-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4908-original-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4908-original-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
