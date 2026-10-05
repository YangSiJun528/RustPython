# Finalization of a global object (#4527)

Original issue: [#4527](https://github.com/RustPython/RustPython/issues/4527)

**Verified closure candidate:** The unchanged original lifetime pattern prints deleted! at interpreter shutdown, with exit 0 and no stderr. An explicit-del control was checked separately.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [4527-original.py](../../evidence/initial16/agent-a/4527-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
class X:
    def __del__(self):
        print("deleted!")


x = X()
```

## Expected and observed results

**Expected:** The global object destructor must run during ordinary interpreter shutdown.

**Observed:** The unchanged original lifetime pattern prints deleted! at interpreter shutdown, with exit 0 and no stderr. An explicit-del control was checked separately.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
deleted!
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
deleted!
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 0</summary>

**stdout:** No output.

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
  '<initial16-audit>/agent-a/4527-original.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<initial16-audit>/agent-a/4527-original.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

The unchanged original lifetime pattern prints deleted! at interpreter shutdown, with exit 0 and no stderr. An explicit-del control was checked separately.

[PR #6934](https://github.com/RustPython/RustPython/pull/6934): module finalization during shutdown.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** Process-abort paths and arbitrary shutdown ordering are not promised.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4527/evidence/metadata.json).
- Historical baseline: [`e5735cde67b8`](https://github.com/RustPython/RustPython/commit/e5735cde67b86699bd68c8959167ecf2649a6f2d), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/4527/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/4527/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[4527-control-cp](../../evidence/initial16/agent-a/4527-control-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4527-control-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4527-control-cp.stderr).
- **[4527-control-rp](../../evidence/initial16/agent-a/4527-control-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4527-control-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4527-control-rp.stderr).
- **[4527-original-cp](../../evidence/initial16/agent-a/4527-original-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4527-original-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4527-original-cp.stderr).
- **[4527-original-rp](../../evidence/initial16/agent-a/4527-original-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4527-original-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4527-original-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
