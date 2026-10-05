# #2527 — REPL expressions inside blocks

Original issue: [#2527](https://github.com/RustPython/RustPython/issues/2527)

**Verified closure candidate:** Actual PTY sessions now display 0–9 from the original loop and 5 from the file-write block. The same CPython input agrees; displayhook and function-scope controls also pass.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

The input is an actual PTY conversation, not a script. The execution record preserves prompt-synchronized input and the merged terminal transcript.

[PTY input and result](../../evidence/initial16/agent-b/fresh-2527-pty-rp.json)

## Expected and observed results

**Expected:** The interactive REPL must display expression values in compound statements.

**Observed:** Actual PTY sessions now display 0–9 from the original loop and 5 from the file-write block. The same CPython input agrees; displayhook and function-scope controls also pass.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>&gt;&gt;&gt; import sys
&gt;&gt;&gt; for i in range(10):
...     i
... 
...
3
4
5
6
7
8
9
&gt;&gt;&gt; with open(&#x27;&lt;initial16-audit&gt;/agent-b/repl-created-&#x27; + sys.implementation.name + &#x27;.txt&#x27;, &#x27;x&#x27;) as f:
...     f.write(&#x27;hello&#x27;)
... 
5
&gt;&gt;&gt; import os; sys.stdout.flush(); sys.stderr.flush(); os._exit(0)</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><pre><code>Welcome to the magnificent Rust Python 0.1.2 interpreter 😱 🖖
No previous history.

[0K&gt;&gt;&gt;&gt;&gt; 
...
[0K&gt;&gt;&gt;&gt;&gt; with open(&#x27;/survey/verification-tools/derived-a/repl-output-1.txt&#x27;, &#x27;w&#x27;) a

s f:

[0K..... 
[6C    f.write(&#x27;hello&#x27;)

[0K..... 
[6C

[0K&gt;&gt;&gt;&gt;&gt; 
[6Cexit()</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><pre><code>[?2026h
[K&gt;&gt;&gt; 
[4C[?2026limport sys
[?2026h
...
[K&gt;&gt;&gt; 
[4C[?2026lwith open(&#x27;&lt;initial16-audit&gt;/agent-b/repl-created-&#x27; + sys.implementation.name + &#x27;.txt&#x27;, &#x27;x&#x27;) as f:
[?2026h
[K... 
[4C[?2026l    f.write(&#x27;hello&#x27;)
[?2026h
[K... 
[4C[?2026l
5
[?2026h
[K&gt;&gt;&gt; 
[4C[?2026limport os; sys.stdout.flush(); sys.stderr.flush(); os._exit(0)</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>See the reused historical record.</code></pre></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-b/saved/current-f39-x86/rustpython -B -S -q
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B -S -q
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

Actual PTY sessions now display 0–9 from the original loop and 5 from the file-write block. The same CPython input agrees; displayhook and function-scope controls also pass.

[PR #7067](https://github.com/RustPython/RustPython/pull/7067): display interactive expressions in nested blocks.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The new run is macOS/Rosetta, not Linux. Earlier Linux PTY evidence is reused separately. A new exclusive file path and os._exit prevent overwriting files or REPL history.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/2527/evidence/metadata.json).
- Historical baseline: [`163cd1953377`](https://github.com/RustPython/RustPython/commit/163cd1953377f4049e06fdae55c715889857a301), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/2527/evidence/historical.stdout.txt).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [fresh-2527-pty-cp](../../evidence/initial16/agent-b/fresh-2527-pty-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-2527-pty-cp.transcript) | in JSON / noted there |
| [fresh-2527-pty-rp](../../evidence/initial16/agent-b/fresh-2527-pty-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-2527-pty-rp.transcript) | in JSON / noted there |
| [fresh-2527-single-cp](../../evidence/initial16/agent-b/fresh-2527-single-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-2527-single-cp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-2527-single-cp.stderr) |
| [fresh-2527-single-rp](../../evidence/initial16/agent-b/fresh-2527-single-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-b/fresh-2527-single-rp.stdout) | [stderr](../../evidence/initial16/agent-b/fresh-2527-single-rp.stderr) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
[?2026h
[K>>> 
[4C[?2026limport sys
[?2026h
[K>>> 
[4C[?2026lfor i in range(10):
[?2026h
[K... 
[4C[?2026l    i
[?2026h
[K... 
[4C[?2026l
0
1
2
3
4
5
6
7
8
9
[?2026h
[K>>> 
[4C[?2026lwith open('<initial16-audit>/agent-b/repl-created-' + sys.implementation.name + '.txt', 'x') as f:
[?2026h
[K... 
[4C[?2026l    f.write('hello')
[?2026h
[K... 
[4C[?2026l
5
[?2026h
[K>>> 
[4C[?2026limport os; sys.stdout.flush(); sys.stderr.flush(); os._exit(0)

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
