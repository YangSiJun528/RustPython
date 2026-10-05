# Py_GIL_DISABLED configuration value (#6429)

Original issue: [#6429](https://github.com/RustPython/RustPython/issues/6429)

**Verified closure candidate:** sysconfig.get_config_var("Py_GIL_DISABLED") is defined as 1 in the verified POSIX RustPython build.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-6429.py](../../evidence/initial16/agent-b/probe-6429.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
import sys, sysconfig

value = sysconfig.get_config_var("Py_GIL_DISABLED")
print(value)
print("type", type(value).__name__)
print("implementation", sys.implementation.name)
print("platform", sys.platform)
print("gil_enabled", getattr(sys, "_is_gil_enabled", lambda: "unavailable")())
```

## Expected and observed results

**Expected:** The tested RustPython build must expose its build-time Py_GIL_DISABLED setting instead of None.

**Observed:** sysconfig.get_config_var("Py_GIL_DISABLED") is defined as 1 in the verified POSIX RustPython build.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
1
type int
implementation rustpython
platform darwin
gil_enabled False
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
0
type int
implementation cpython
platform darwin
gil_enabled True
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 0</summary>

**stdout:**

```text
None
```

**stderr:**

```text
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-b/saved/current-f39-x86/rustpython' -B -S \
  '<initial16-audit>/agent-b/probe-6429.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B -S \
  '<initial16-audit>/agent-b/probe-6429.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

sysconfig.get_config_var("Py_GIL_DISABLED") is defined as 1 in the verified POSIX RustPython build.

[PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose the build-time Py_GIL_DISABLED value.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** CPython can legitimately return a different value. This is not proof of full free-threading or C-extension compatibility.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/6429/evidence/metadata.json).
- Historical baseline: [`e227956a58f0`](https://github.com/RustPython/RustPython/commit/e227956a58f0f072f8be177264e0fdc1b9280e8a), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/6429/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/6429/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[fresh-6429-cp](../../evidence/initial16/agent-b/fresh-6429-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-6429-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-6429-cp.stderr).
- **[fresh-6429-rp](../../evidence/initial16/agent-b/fresh-6429-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-6429-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-6429-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
