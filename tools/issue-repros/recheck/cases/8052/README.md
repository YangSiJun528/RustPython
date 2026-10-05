# #8052 — Ellipsis type name

Original issue: [#8052](https://github.com/RustPython/RustPython/issues/8052)

**Verified closure candidate:** The name and repr are `ellipsis` and `<class 'ellipsis'>`; the types alias, JSON error note and existing JSON regression tests also pass.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-8052.py](../../evidence/initial16/agent-b/probe-8052.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
import types, json, collections

print(type(...).__name__)
print(repr(type(...)))
print("alias", types.EllipsisType is type(...))


def default(obj):
    if obj is NotImplemented:
        raise ValueError
    if obj is ...:
        return NotImplemented
    if obj is type:
        return collections
    return [...]


try:
    json.dumps(type, default=default)
except ValueError as e:
    print("notes", e.__notes__)
```

## Expected and observed results

**Expected:** The Ellipsis singleton type must use the CPython-visible name ellipsis.

**Observed:** The name and repr are `ellipsis` and `<class 'ellipsis'>`; the types alias, JSON error note and existing JSON regression tests also pass.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>ellipsis
&lt;class &#x27;ellipsis&#x27;&gt;
alias True
notes [&#x27;when serializing ellipsis object&#x27;, &#x27;when serializing list item 0&#x27;, &#x27;when serializing module object&#x27;, &#x27;when serializing type object&#x27;]</code></pre></td><td valign="top"><pre><code>EllipsisType
&lt;class &#x27;EllipsisType&#x27;&gt;</code></pre></td><td valign="top"><pre><code>ellipsis
&lt;class &#x27;ellipsis&#x27;&gt;
alias True
notes [&#x27;when serializing ellipsis object&#x27;, &#x27;when serializing list item 0&#x27;, &#x27;when serializing module object&#x27;, &#x27;when serializing type object&#x27;]</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-b/saved/current-f39-x86/rustpython -B -S <initial16-audit>/agent-b/probe-8052.py
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B -S <initial16-audit>/agent-b/probe-8052.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

The name and repr are `ellipsis` and `<class 'ellipsis'>`; the types alias, JSON error note and existing JSON regression tests also pass.

[PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** No first-fixing revision was determined.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/8052/evidence/metadata.json).
- Historical baseline: [`83fe92042112`](https://github.com/RustPython/RustPython/commit/83fe92042112f9db89a70495b552ab433d77e751), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/8052/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/8052/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [fresh-8052-cp](../../evidence/initial16/agent-b/fresh-8052-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-8052-cp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-8052-cp.stderr) |
| [fresh-8052-rp](../../evidence/initial16/agent-b/fresh-8052-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-8052-rp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-8052-rp.stderr) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
ellipsis
<class 'ellipsis'>
alias True
notes ['when serializing ellipsis object', 'when serializing list item 0', 'when serializing module object', 'when serializing type object']

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
