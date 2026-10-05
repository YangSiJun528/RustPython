# #4613 — Locale support for FormatSpec n

Original issue: [#4613](https://github.com/RustPython/RustPython/issues/4613)

**Partially resolved — do not close:** Basic n and the original locale tests pass. Across five available locales, 395 formatting results include 102 differences: 84 zero-padding cases and 18 other Unicode-separator width cases.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-locale-unicode-width.py](../../evidence/additional11/agent-b/probe-locale-unicode-width.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
import locale
import json

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
conv = locale.localeconv()
plain = format(1234, "n")
padded = format(1234, ">20n")
print(
    json.dumps(
        {
            "locale": locale.setlocale(locale.LC_ALL),
            "conv": {
                k: conv[k] for k in ("decimal_point", "thousands_sep", "grouping")
            },
            "plain": plain,
            "plain_characters": len(plain),
            "plain_bytes": len(plain.encode()),
            "padded": padded,
            "padded_characters": len(padded),
            "padded_bytes": len(padded.encode()),
        },
        indent=2,
    )
)
assert len(padded) == 20, "Locale separator must count as one character in field width"
```

## Expected and observed results

**Expected:** Locale-sensitive n formatting must preserve grouping and character-based field width.

**Observed:** Basic n and the original locale tests pass. Across five available locales, 395 formatting results include 102 differences: 84 zero-padding cases and 18 other Unicode-separator width cases.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>{
  &quot;locale&quot;: &quot;fr_FR.UTF-8&quot;,
  &quot;conv&quot;: {
    &quot;decimal_point&quot;: &quot;,&quot;,
...
    &quot;grouping&quot;: [
      3,
      0
    ]
  },
  &quot;plain&quot;: &quot;1\u202f234&quot;,
  &quot;plain_characters&quot;: 5,
  &quot;plain_bytes&quot;: 7,
  &quot;padded&quot;: &quot;               1\u202f234&quot;,
  &quot;padded_characters&quot;: 20,
  &quot;padded_bytes&quot;: 22
}</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><pre><code>CATALOG_RECORD {&quot;kind&quot;: &quot;start&quot;, &quot;case_id&quot;: &quot;issue-4613-case-01&quot;, &quot;selector&quot;: &quot;test.test_types.TypesTests.{test_float__format__locale,test_int__format__locale}&quot;, &quot;interpreter&quot;: &quot;3.11.0alpha (tags/v0.2.0-311-ga7c985685:a7c985685, Mar  2 2023, 15:34:45) \n[rustc 1.67.1]&quot;, &quot;executable&quot;: &quot;&lt;survey&gt;/.build/slot-a/release/rustpython&quot;, &quot;cwd&quot;: &quot;&lt;survey&gt;/logs/scratch-history-a/a7c9856851&quot;, &quot;selector_derivation&quot;: &quot;Exact locale n-format tests referenced through issue4613/PR4609, now lines433\u2013448. Run with en_US.UTF-8 installed and LC_ALL unset; retain run_with_locale wrapper. Log actual locale so fallback C locale cannot masquerade as locale-grouping proof.&quot;, &quot;original_selector&quot;: null, &quot;derivation&quot;: &quot;TODO RustPython skip decorators bypassed in memory; targeted expectedFailure flags cleared&quot;}
CATALOG_RECORD {&quot;kind&quot;: &quot;selection&quot;, &quot;case_id&quot;: &quot;issue-4613-case-01&quot;, &quot;selected_ids&quot;: [&quot;test.test_types.TypesTests.test_float__format__locale&quot;, &quot;test.test_types.TypesTests.test_int__format__locale&quot;], &quot;loader_errors&quot;: [], &quot;module_origin&quot;: &quot;&lt;workspace&gt;/pylib/Lib/test/test_types.py&quot;, &quot;module_sha256&quot;: &quot;18f8783da5a0ce95f3dda32f99829f506161a11a3e11c035a6bbdaac02fe19ed&quot;, &quot;bypassed_decorators&quot;: [{&quot;kind&quot;: &quot;skip&quot;, &quot;object&quot;: &quot;test.test_types.TypesTests.test_int__format__locale&quot;, &quot;reason&quot;: &quot;TODO: RustPython format code n is not integrated with locale&quot;, &quot;action&quot;: &quot;decoration-time identity; original body and other decorators retained&quot;}, {&quot;kind&quot;: &quot;expectedFailure_preserved&quot;, &quot;object&quot;: &quot;test.test_types.TypesTests.test_float__format__locale&quot;, &quot;action&quot;: &quot;No explicit RustPython marker in declaration prefix; pres</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><pre><code>{
  &quot;locale&quot;: &quot;fr_FR.UTF-8&quot;,
  &quot;conv&quot;: {
    &quot;decimal_point&quot;: &quot;,&quot;,
...
    &quot;grouping&quot;: [
      3,
      0
    ]
  },
  &quot;plain&quot;: &quot;1\u202f234&quot;,
  &quot;plain_characters&quot;: 5,
  &quot;plain_bytes&quot;: 7,
  &quot;padded&quot;: &quot;             1\u202f234&quot;,
  &quot;padded_characters&quot;: 18,
  &quot;padded_bytes&quot;: 20
}</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
test_float__format__locale (test.test_types.TypesTests.test_float__format__locale) ... expected failure
test_int__format__locale (test.test_types.TypesTests.test_int__format__locale) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.004s

OK (expected failures=1)</code></pre></td><td valign="top"><pre><code>Traceback (most recent call last):
  File &quot;&lt;additional11-audit&gt;/agent-b/probe-locale-unicode-width.py&quot;, line 12, in &lt;module&gt;
    assert len(padded) == 20, &#x27;Locale separator must count as one character in field width&#x27;
           ^^^^^^^^^^^^^^^^^
AssertionError: Locale separator must count as one character in field width</code></pre></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>1</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-b/saved/current-f39-x86/rustpython -B <additional11-audit>/agent-b/probe-locale-unicode-width.py
```

CPython reference command:

```sh
<home>/.local/bin/python3 -B <additional11-audit>/agent-b/probe-locale-unicode-width.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

Basic n and the original locale tests pass. Across five available locales, 395 formatting results include 102 differences: 84 zero-padding cases and 18 other Unicode-separator width cases.

[PR #7350](https://github.com/RustPython/RustPython/pull/7350): use locale grouping, separator and decimal-point data.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The zero-padding defect was rerun on native ARM64 too. The fr_FR U+202F width counterexample was run with Rosetta RustPython; >20n produces 18 characters rather than 20.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`a7c985685146`](https://github.com/RustPython/RustPython/commit/a7c985685146ca401011eb0c25c0b2805a767ce7), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-catalog-a7c9856851-scratch.stdout](../../evidence/history/logs/issue-4613-case-01/historical-catalog-a7c9856851-scratch.stdout).
- [Full reused historical-catalog-a7c9856851-scratch.stderr](../../evidence/history/logs/issue-4613-case-01/historical-catalog-a7c9856851-scratch.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [4613-cross-cpython](../../evidence/additional11/agent-a/4613-cross-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/4613-cross-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/4613-cross-cpython.stderr.txt) |
| [4613-cross-rustpython](../../evidence/additional11/agent-a/4613-cross-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/4613-cross-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/4613-cross-rustpython.stderr.txt) |
| [4613-unicode-width-cpython](../../evidence/additional11/agent-b/4613-unicode-width-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/4613-unicode-width-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/4613-unicode-width-cpython.stderr.txt) |
| [4613-unicode-width-rustpython](../../evidence/additional11/agent-b/4613-unicode-width-rustpython.json) | 1 | false | [stdout](../../evidence/additional11/agent-b/4613-unicode-width-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/4613-unicode-width-rustpython.stderr.txt) |
| [4613-zero-padding-cpython](../../evidence/additional11/agent-b/4613-zero-padding-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/4613-zero-padding-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/4613-zero-padding-cpython.stderr.txt) |
| [4613-zero-padding-rustpython](../../evidence/additional11/agent-b/4613-zero-padding-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/4613-zero-padding-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/4613-zero-padding-rustpython.stderr.txt) |
| [locale-matrix-cpython](../../evidence/additional11/agent-b/locale-matrix-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-matrix-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-matrix-cpython.stderr.txt) |
| [locale-matrix-rustpython](../../evidence/additional11/agent-b/locale-matrix-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-matrix-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-matrix-rustpython.stderr.txt) |
| [locale-original-set-cpython](../../evidence/additional11/agent-b/locale-original-set-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-original-set-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-original-set-cpython.stderr.txt) |
| [locale-original-set-rustpython](../../evidence/additional11/agent-b/locale-original-set-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-original-set-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-original-set-rustpython.stderr.txt) |
| [locale-original-unset-cpython](../../evidence/additional11/agent-b/locale-original-unset-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-original-unset-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-original-unset-cpython.stderr.txt) |
| [locale-original-unset-rustpython](../../evidence/additional11/agent-b/locale-original-unset-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-original-unset-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-original-unset-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
{
  "locale": "fr_FR.UTF-8",
  "conv": {
    "decimal_point": ",",
    "thousands_sep": "\u202f",
    "grouping": [
      3,
      0
    ]
  },
  "plain": "1\u202f234",
  "plain_characters": 5,
  "plain_bytes": 7,
  "padded": "             1\u202f234",
  "padded_characters": 18,
  "padded_bytes": 20
}

```

**stderr:**

```text
Traceback (most recent call last):
  File "<additional11-audit>/agent-b/probe-locale-unicode-width.py", line 12, in <module>
    assert len(padded) == 20, 'Locale separator must count as one character in field width'
           ^^^^^^^^^^^^^^^^^
AssertionError: Locale separator must count as one character in field width

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
