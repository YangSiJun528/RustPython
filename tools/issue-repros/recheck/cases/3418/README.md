# Native OrderedDict export (#3418)

Original issue: [#3418](https://github.com/RustPython/RustPython/issues/3418)

**Verified closure candidate:** The native import succeeds, and ordering, move_to_end, popitem, reversed, equality and a subclass sample agree with CPython.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [3418-original.py](../../evidence/initial16/agent-a/3418-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
from _collections import OrderedDict
```

## Expected and observed results

**Expected:** from _collections import OrderedDict must expose the native implementation.

**Observed:** The native import succeeds, and ordering, move_to_end, popitem, reversed, equality and a subclass sample agree with CPython.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:** No output.

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:** No output.

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:** No output.

**stderr:**

```text
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
Traceback (most recent call last):
  File "<survey>/repros/3418/issue-3418-case-01/source-01.py", line 1, in <module>
    from _collections  import OrderedDict
ImportError: cannot import name 'OrderedDict'
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B \
  '<initial16-audit>/agent-a/3418-original.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<initial16-audit>/agent-a/3418-original.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

The native import succeeds, and ordering, move_to_end, popitem, reversed, equality and a subclass sample agree with CPython.

[PR #8780](https://github.com/RustPython/RustPython/pull/8780): native OrderedDict and class-method descriptors.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** This verifies the reported native export and exercised operations, not all OrderedDict behavior.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/3418/evidence/metadata.json).
- Historical baseline: [`40fd9c2683d7`](https://github.com/RustPython/RustPython/commit/40fd9c2683d76adf2b9ed0d77c055e2d2514c27d), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/3418/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/3418/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[3418-boundaries-cp](../../evidence/initial16/agent-a/3418-boundaries-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/3418-boundaries-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/3418-boundaries-cp.stderr).
- **[3418-boundaries-rp](../../evidence/initial16/agent-a/3418-boundaries-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/3418-boundaries-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/3418-boundaries-rp.stderr).
- **[3418-original-cp](../../evidence/initial16/agent-a/3418-original-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/3418-original-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/3418-original-cp.stderr).
- **[3418-original-rp](../../evidence/initial16/agent-a/3418-original-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/3418-original-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/3418-original-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
