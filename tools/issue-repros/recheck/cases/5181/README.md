# #5181 — Locale-aware n formatting

Original issue: [#5181](https://github.com/RustPython/RustPython/issues/5181)

**Partially resolved — do not close:** Bare n and the original locale test pass, but en_US format(123456789, "015n") gives 0000123,456,789 instead of CPython's 000,123,456,789.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-5181-width.py](../../evidence/initial16/agent-b/probe-5181-width.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
import locale

for name in ["en_US.UTF-8", "de_DE.UTF-8", "hi_IN.UTF-8"]:
    locale.setlocale(locale.LC_ALL, name)
    text = format(123456789, "015n")
    print(name, repr(text), len(text))
```

## Expected and observed results

**Expected:** Locale grouping must also remain correct when n formatting is combined with zero padding.

**Observed:** Bare n and the original locale test pass, but en_US format(123456789, "015n") gives 0000123,456,789 instead of CPython's 000,123,456,789.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>en_US.UTF-8 &#x27;000,123,456,789&#x27; 15
de_DE.UTF-8 &#x27;000.123.456.789&#x27; 15
hi_IN.UTF-8 &#x27;00,12,34,56,789&#x27; 15</code></pre></td><td valign="top"><pre><code>locale en_US.UTF-8
result &#x27;123456789&#x27;
matches False</code></pre></td><td valign="top"><pre><code>en_US.UTF-8 &#x27;0000123,456,789&#x27; 15
de_DE.UTF-8 &#x27;0000123.456.789&#x27; 15
hi_IN.UTF-8 &#x27;00012,34,56,789&#x27; 15</code></pre></td></tr>
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
<survey>/.build/slot-b/saved/current-f39-x86/rustpython -B -S <initial16-audit>/agent-b/probe-5181-width.py
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B -S <initial16-audit>/agent-b/probe-5181-width.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

Bare n and the original locale test pass, but en_US format(123456789, "015n") gives 0000123,456,789 instead of CPython's 000,123,456,789.

[PR #7350](https://github.com/RustPython/RustPython/pull/7350): use locale grouping, separator and decimal-point data.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The locale exists and grouping is active. Both outputs have length 15; the defect is grouping, not missing locale setup.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/5181/evidence/metadata.json).
- Historical baseline: [`a8ab7dd38814`](https://github.com/RustPython/RustPython/commit/a8ab7dd3881437ad2eef31b3470427db20656a84), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/5181/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/5181/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [fresh-5181-cp](../../evidence/initial16/agent-b/fresh-5181-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-5181-cp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-5181-cp.stderr) |
| [fresh-5181-rp](../../evidence/initial16/agent-b/fresh-5181-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-5181-rp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-5181-rp.stderr) |
| [fresh-5181-width-cp](../../evidence/initial16/agent-b/fresh-5181-width-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-5181-width-cp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-5181-width-cp.stderr) |
| [fresh-5181-width-rp](../../evidence/initial16/agent-b/fresh-5181-width-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-5181-width-rp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-5181-width-rp.stderr) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
en_US.UTF-8 '0000123,456,789' 15
de_DE.UTF-8 '0000123.456.789' 15
hi_IN.UTF-8 '00012,34,56,789' 15

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
