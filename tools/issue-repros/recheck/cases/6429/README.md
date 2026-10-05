# #6429 — Py_GIL_DISABLED configuration value

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

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>0
type int
implementation cpython
platform darwin
gil_enabled True</code></pre></td><td valign="top"><pre><code>None</code></pre></td><td valign="top"><pre><code>1
type int
implementation rustpython
platform darwin
gil_enabled False</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object</code></pre></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-b/saved/current-f39-x86/rustpython -B -S <initial16-audit>/agent-b/probe-6429.py
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B -S <initial16-audit>/agent-b/probe-6429.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

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

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [fresh-6429-cp](../../evidence/initial16/agent-b/fresh-6429-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-6429-cp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-6429-cp.stderr) |
| [fresh-6429-rp](../../evidence/initial16/agent-b/fresh-6429-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-6429-rp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-6429-rp.stderr) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
1
type int
implementation rustpython
platform darwin
gil_enabled False

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
