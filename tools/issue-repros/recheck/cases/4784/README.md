# #4784 — README API documentation link

Original issue: [#4784](https://github.com/RustPython/RustPython/issues/4784)

**Verified closure candidate:** The README destination returned HTTP 200 and an actual RustPython 0.6.0 API page, including crate and API content; status alone was not the oracle.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

This is an HTTP destination/content check. No Python interpreter comparison applies.

## Expected and observed results

**Expected:** The README link must serve API documentation rather than an error or generic page.

**Observed:** The README destination returned HTTP 200 and an actual RustPython 0.6.0 API page, including crate and API content; status alone was not the oracle.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>N/A</code></pre></td><td valign="top"><pre><code>Original report: destination was not API documentation.</code></pre></td><td valign="top"><pre><code>status=200
url=https://docs.rs/rustpython/latest/rustpython/</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><pre><code>N/A</code></pre></td><td valign="top"><pre><code>No interpreter comparison applies.</code></pre></td><td valign="top"><pre><code>curl progress meter only (captured in tool transcript, not a separate file)</code></pre></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>N/A</code></pre></td><td valign="top"><pre><code>N/A</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
curl --location --max-time 30 --output <initial16-audit>/agent-b/fresh-4784-docs.html --dump-header <initial16-audit>/agent-b/fresh-4784-headers.txt --write-out 'status=%{http_code}\nurl=%{url_effective}\n' https://docs.rs/rustpython
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

The README destination returned HTTP 200 and an actual RustPython 0.6.0 API page, including crate and API content; status alone was not the oracle.

[Published API documentation](https://docs.rs/rustpython/latest/rustpython/).

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** This is the externally served page observed on October 5, 2026, not a documentation build from the baseline commit. CPython comparison does not apply.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This is an HTTP observation; interpreter architecture does not apply.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4784/README.md).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [fresh-4784-http](../../evidence/initial16/agent-b/fresh-4784-http.json) | 0 | false | in JSON / noted there | in JSON / noted there |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
status=200
url=https://docs.rs/rustpython/latest/rustpython/

```

**stderr:**

```text
curl progress meter only (captured in tool transcript, not a separate file)
```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
