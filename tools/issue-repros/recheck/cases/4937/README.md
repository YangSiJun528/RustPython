# #4937 — Email Subject with an unknown encoding

Original issue: [#4937](https://github.com/RustPython/RustPython/issues/4937)

**Verified closure candidate:** The original X-encoded Subject is returned without KeyError. Unknown encodings and related malformed-header controls were also checked.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [4937-original.py](../../evidence/initial16/agent-a/4937-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
import email
import email.policy

mytext = "Subject:=?us-ascii?X?value?="
em = email.message_from_string(mytext, policy=email.policy.default)
em.get("Subject")
```

## Expected and observed results

**Expected:** Retrieving the reported Subject must recover from the unknown encoded-word encoding.

**Observed:** The original X-encoded Subject is returned without KeyError. Unknown encodings and related malformed-header controls were also checked.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
...
    kwds[&#x27;parse_tree&#x27;] = cls.value_parser(value)
  File &quot;&lt;historical-checkout&gt;/pylib/Lib/email/_header_value_parser.py&quot;, line 1498, in get_unstructured
    pass
  File &quot;&lt;historical-checkout&gt;/pylib/Lib/email/_header_value_parser.py&quot;, line 1494, in get_unstructured
    token, value = get_encoded_word(value)
  File &quot;&lt;historical-checkout&gt;/pylib/Lib/email/_header_value_parser.py&quot;, line 1447, in get_encoded_word
    &quot;encoded word format invalid: &#x27;{}&#x27;&quot;.format(ew.cte))
  File &quot;&lt;historical-checkout&gt;/pylib/Lib/email/_header_value_parser.py&quot;, line 1444, in get_encoded_word
    text, charset, lang, defects = _ew.decode(&#x27;=?&#x27; + tok + &#x27;?=&#x27;)
  File &quot;&lt;historical-checkout&gt;/pylib/Lib/email/_encoded_words.py&quot;, line 166, in decode
    bstring, defects = _cte_decoders[cte](bstring)
KeyError: x</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <initial16-audit>/agent-a/4937-original.py
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <initial16-audit>/agent-a/4937-original.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

The original X-encoded Subject is returned without KeyError. Unknown encodings and related malformed-header controls were also checked.

[PR #5663](https://github.com/RustPython/RustPython/pull/5663): unknown encoded-word recovery.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** Successful recovery is not a guarantee for every malformed email header.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4937/evidence/metadata.json).
- Historical baseline: [`02840593bc56`](https://github.com/RustPython/RustPython/commit/02840593bc56ae416ba2646166628f1712d6cf43), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/4937/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/4937/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [4937-boundaries-cp](../../evidence/initial16/agent-a/4937-boundaries-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4937-boundaries-cp.stdout) | [stderr](../../evidence/initial16/agent-a/4937-boundaries-cp.stderr) |
| [4937-boundaries-rp](../../evidence/initial16/agent-a/4937-boundaries-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4937-boundaries-rp.stdout) | [stderr](../../evidence/initial16/agent-a/4937-boundaries-rp.stderr) |
| [4937-original-cp](../../evidence/initial16/agent-a/4937-original-cp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4937-original-cp.stdout) | [stderr](../../evidence/initial16/agent-a/4937-original-cp.stderr) |
| [4937-original-rp](../../evidence/initial16/agent-a/4937-original-rp.json) | 0 | false | [stdout](../../evidence/initial16/agent-a/4937-original-rp.stdout) | [stderr](../../evidence/initial16/agent-a/4937-original-rp.stderr) |

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
