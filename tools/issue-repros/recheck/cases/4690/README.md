# #4690 — Native class-method descriptor type

Original issue: [#4690](https://github.com/RustPython/RustPython/issues/4690)

**Verified closure candidate:** Both original descriptor queries return classmethod_descriptor. Binding and representative additional native descriptors agree with CPython.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [4690-original.py](../../evidence/initial16/agent-a/4690-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
print(type(dict.__dict__["fromkeys"]))
print(type(dict.fromkeys))
```

## Expected and observed results

**Expected:** Native class methods must use the classmethod_descriptor type.

**Observed:** Both original descriptor queries return classmethod_descriptor. Binding and representative additional native descriptors agree with CPython.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>&lt;class &#x27;classmethod_descriptor&#x27;&gt;
&lt;class &#x27;builtin_function_or_method&#x27;&gt;</code></pre></td><td valign="top"><pre><code>classmethod
method</code></pre></td><td valign="top"><pre><code>&lt;class &#x27;classmethod_descriptor&#x27;&gt;
&lt;class &#x27;builtin_function_or_method&#x27;&gt;</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object</code></pre></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <initial16-audit>/agent-a/4690-original.py
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <initial16-audit>/agent-a/4690-original.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

Both original descriptor queries return classmethod_descriptor. Binding and representative additional native descriptors agree with CPython.

[PR #8780](https://github.com/RustPython/RustPython/pull/8780): native OrderedDict and class-method descriptors.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** No claim is made about every descriptor or every introspection API.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4690/evidence/metadata.json).
- Historical baseline: [`8ff947e83a65`](https://github.com/RustPython/RustPython/commit/8ff947e83a65b74c920edc63aed8a0a5854b8612), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/4690/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/4690/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [4690-boundaries-cp](../../evidence/initial16/agent-a/4690-boundaries-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4690-boundaries-cp.stdout) | [stderr](../../evidence/initial16/agent-a/4690-boundaries-cp.stderr) |
| [4690-boundaries-rp](../../evidence/initial16/agent-a/4690-boundaries-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4690-boundaries-rp.stdout) | [stderr](../../evidence/initial16/agent-a/4690-boundaries-rp.stderr) |
| [4690-original-cp](../../evidence/initial16/agent-a/4690-original-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4690-original-cp.stdout) | [stderr](../../evidence/initial16/agent-a/4690-original-cp.stderr) |
| [4690-original-rp](../../evidence/initial16/agent-a/4690-original-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4690-original-rp.stdout) | [stderr](../../evidence/initial16/agent-a/4690-original-rp.stderr) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
<class 'classmethod_descriptor'>
<class 'builtin_function_or_method'>

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
