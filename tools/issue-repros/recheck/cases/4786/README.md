# Surrogate in a type name (#4786)

Original issue: [#4786](https://github.com/RustPython/RustPython/issues/4786)

**Verified closure candidate:** The original surrogate is retained and type creation raises UnicodeEncodeError, matching CPython. Exit 1 for the uncaught exception is expected.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [4786-original.py](../../evidence/initial16/agent-a/4786-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
type("A\udcdcB", (), {})
```

## Expected and observed results

**Expected:** A surrogate-containing type name must raise UnicodeEncodeError instead of being silently replaced.

**Observed:** The original surrogate is retained and type creation raises UnicodeEncodeError, matching CPython. Exit 1 for the uncaught exception is expected.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 1</summary>

**stdout:** No output.

**stderr:**

```text
Traceback (most recent call last):
  File "<initial16-audit>/agent-a/4786-original.py", line 1, in <module>
    type("A\udcdcB", (), {})
    ~~~~^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcdc' in position 1: surrogates not allowed
```

</details>

<details>
<summary>CPython 3.14.6 — exit 1</summary>

**stdout:** No output.

**stderr:**

```text
Traceback (most recent call last):
  File "<initial16-audit>/agent-a/4786-original.py", line 1, in <module>
    type("A\udcdcB", (), {})
    ~~~~^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcdc' in position 1: surrogates not allowed
```

</details>

<details>
<summary>RustPython before (reused) — exit 0</summary>

**stdout:**

```text
<class '__main__.A�B'>
```

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B \
  '<initial16-audit>/agent-a/4786-original.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<initial16-audit>/agent-a/4786-original.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

The original surrogate is retained and type creation raises UnicodeEncodeError, matching CPython. Exit 1 for the uncaught exception is expected.

[PR #5629](https://github.com/RustPython/RustPython/pull/5629): retain surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** A separate adjacent-surrogate input is rejected by both, but UnicodeEncodeError.end differs (2 versus 3). Full error-span parity is not claimed.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4786/evidence/metadata.json).
- Historical baseline: [`010640ccc8f7`](https://github.com/RustPython/RustPython/commit/010640ccc8f74f56075df09a654352ae3d162d25), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/4786/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/4786/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[4786-boundaries-cp](../../evidence/initial16/agent-a/4786-boundaries-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4786-boundaries-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4786-boundaries-cp.stderr).
- **[4786-boundaries-rp](../../evidence/initial16/agent-a/4786-boundaries-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4786-boundaries-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4786-boundaries-rp.stderr).
- **[4786-original-cp](../../evidence/initial16/agent-a/4786-original-cp.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4786-original-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4786-original-cp.stderr).
- **[4786-original-rp](../../evidence/initial16/agent-a/4786-original-rp.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4786-original-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4786-original-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
