# #5656 — Invalid escape warning in a bytes literal

Original issue: [#5656](https://github.com/RustPython/RustPython/issues/5656)

**Verified closure candidate:** The bytes value is preserved and compilation emits the required SyntaxWarning for the invalid escape. Warning presence and warning-as-error behavior were checked.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [5656-original.py](../../evidence/initial16/agent-a/5656-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
assert b"omkmok\Xaa" == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])
```

## Expected and observed results

**Expected:** Compilation of the original bytes literal must report the invalid escape while preserving its value.

**Observed:** The bytes value is preserved and compilation emits the required SyntaxWarning for the invalid escape. Warning presence and warning-as-error behavior were checked.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td></tr>
<tr><th>stderr</th><td valign="top"><pre><code>&lt;initial16-audit&gt;/agent-a/5656-original.py:1: SyntaxWarning: &quot;\X&quot; is an invalid escape sequence. Such sequences will not work in the future. Did you mean &quot;\\X&quot;? A raw string is also an option.
  assert b&quot;omkmok\Xaa&quot; == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])</code></pre></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
...
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><pre><code>&lt;initial16-audit&gt;/agent-a/5656-original.py:1: SyntaxWarning: &quot;\X&quot; is an invalid escape sequence. Such sequences will not work in the future. Did you mean &quot;\\X&quot;? A raw string is also an option.
  assert b&quot;omkmok\Xaa&quot; == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])</code></pre></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <initial16-audit>/agent-a/5656-original.py
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <initial16-audit>/agent-a/5656-original.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

The bytes value is preserved and compilation emits the required SyntaxWarning for the invalid escape. Warning presence and warning-as-error behavior were checked.

[PR #7164](https://github.com/RustPython/RustPython/pull/7164): warn about invalid string and bytes escapes.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** Exit 0 alone is not the oracle; warning output is required.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/5656/evidence/metadata.json).
- Historical baseline: [`c3ed002b1204`](https://github.com/RustPython/RustPython/commit/c3ed002b1204d9ff156b5192b634a4056101b255), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/5656/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/5656/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [5656-boundaries-cp](../../evidence/initial16/agent-a/5656-boundaries-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/5656-boundaries-cp.stdout) | [stderr](../../evidence/initial16/agent-a/5656-boundaries-cp.stderr) |
| [5656-boundaries-rp](../../evidence/initial16/agent-a/5656-boundaries-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/5656-boundaries-rp.stdout) | [stderr](../../evidence/initial16/agent-a/5656-boundaries-rp.stderr) |
| [5656-original-cp](../../evidence/initial16/agent-a/5656-original-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/5656-original-cp.stdout) | [stderr](../../evidence/initial16/agent-a/5656-original-cp.stderr) |
| [5656-original-rp](../../evidence/initial16/agent-a/5656-original-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/5656-original-rp.stdout) | [stderr](../../evidence/initial16/agent-a/5656-original-rp.stderr) |
| [5656-whole-snippet-cp](../../evidence/initial16/agent-a/5656-whole-snippet-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/5656-whole-snippet-cp.stdout) | [stderr](../../evidence/initial16/agent-a/5656-whole-snippet-cp.stderr) |
| [5656-whole-snippet-rp](../../evidence/initial16/agent-a/5656-whole-snippet-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/5656-whole-snippet-rp.stdout) | [stderr](../../evidence/initial16/agent-a/5656-whole-snippet-rp.stderr) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text

```

**stderr:**

```text
<initial16-audit>/agent-a/5656-original.py:1: SyntaxWarning: "\X" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\X"? A raw string is also an option.
  assert b"omkmok\Xaa" == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
