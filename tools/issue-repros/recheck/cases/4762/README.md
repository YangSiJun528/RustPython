# #4762 — Negative dynamic format width

Original issue: [#4762](https://github.com/RustPython/RustPython/issues/4762)

**Verified closure candidate:** The original assertion preserves the two trailing spaces in `'abc  '`. Positive, zero and additional negative-width controls also agree with CPython.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [4762-original.py](../../evidence/initial16/agent-a/4762-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
assert "%*s" % (-5, "abc") == "abc  "
```

## Expected and observed results

**Expected:** A negative dynamic width selects left alignment.

**Observed:** The original assertion preserves the two trailing spaces in `'abc  '`. Positive, zero and additional negative-width controls also agree with CPython.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
Traceback (most recent call last):
  File &quot;&lt;survey&gt;/repros/4762/issue-4762-case-01/source-01.py&quot;, line 1, in &lt;module&gt;
    assert(&#x27;%*s&#x27; % (-5, &#x27;abc&#x27;) == &#x27;abc  &#x27;)
AssertionError</code></pre></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <initial16-audit>/agent-a/4762-original.py
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <initial16-audit>/agent-a/4762-original.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

The original assertion preserves the two trailing spaces in `'abc  '`. Positive, zero and additional negative-width controls also agree with CPython.

[PR #4766](https://github.com/RustPython/RustPython/pull/4766): left alignment for negative dynamic widths.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The checked formatting cases do not establish every formatting combination.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4762/evidence/metadata.json).
- Historical baseline: [`c36e3612e7dd`](https://github.com/RustPython/RustPython/commit/c36e3612e7dd1c7abd9fc7b76b912372bd26afbf), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/4762/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/4762/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [4762-boundaries-cp](../../evidence/initial16/agent-a/4762-boundaries-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4762-boundaries-cp.stdout) | [stderr](../../evidence/initial16/agent-a/4762-boundaries-cp.stderr) |
| [4762-boundaries-rp](../../evidence/initial16/agent-a/4762-boundaries-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4762-boundaries-rp.stdout) | [stderr](../../evidence/initial16/agent-a/4762-boundaries-rp.stderr) |
| [4762-original-cp](../../evidence/initial16/agent-a/4762-original-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4762-original-cp.stdout) | [stderr](../../evidence/initial16/agent-a/4762-original-cp.stderr) |
| [4762-original-rp](../../evidence/initial16/agent-a/4762-original-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4762-original-rp.stdout) | [stderr](../../evidence/initial16/agent-a/4762-original-rp.stderr) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
