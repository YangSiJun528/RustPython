# #4970 — Locale formatting with LC_ALL unset

Original issue: [#4970](https://github.com/RustPython/RustPython/issues/4970)

**Verified closure candidate:** With LC_ALL absent and LANG/LC_NUMERIC=en_US.UTF-8, the unmodified original test_locale and two int/float locale tests pass, with no skip or expectedFailure.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-original-locale-tests.py](../../evidence/additional11/agent-b/probe-original-locale-tests.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
import sys
import os
import json
import locale
import unittest

# CPython imports the identical repository test source, while retaining its own stdlib.
test_parent = "<slot-b-source>/Lib"
import types

test_package = types.ModuleType("test")
test_package.__path__ = [test_parent + "/test"]
test_package.__file__ = test_parent + "/test/__init__.py"
sys.modules["test"] = test_package
from test import test_format, test_types

effective = locale.setlocale(locale.LC_ALL, "")
conv = locale.localeconv()
print(
    json.dumps(
        {
            "LC_ALL_environment": os.environ.get("LC_ALL"),
            "LANG": os.environ.get("LANG"),
            "LC_NUMERIC": os.environ.get("LC_NUMERIC"),
            "effective": effective,
            "conv": {
                k: conv[k] for k in ("decimal_point", "thousands_sep", "grouping")
            },
            "integer": format(123456789, "n"),
            "float": format(1234.5, "n"),
            "test_files": [test_format.__file__, test_types.__file__],
        },
        indent=2,
    ),
    flush=True,
)
assert conv["grouping"], (
    "A grouping locale must be active to reach the original assertion"
)
suite = unittest.TestSuite(
    [
        test_format.FormatTest("test_locale"),
        test_types.TypesTests("test_int__format__locale"),
        test_types.TypesTests("test_float__format__locale"),
    ]
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
assert result.testsRun == 3
assert (
    not result.skipped
    and not result.expectedFailures
    and not result.unexpectedSuccesses
)
assert result.wasSuccessful()
```

## Expected and observed results

**Expected:** The original test must use locale grouping after setlocale(LC_ALL, "") even when LC_ALL is absent from the environment.

**Observed:** With LC_ALL absent and LANG/LC_NUMERIC=en_US.UTF-8, the unmodified original test_locale and two int/float locale tests pass, with no skip or expectedFailure.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>{
  &quot;LC_ALL_environment&quot;: null,
  &quot;LANG&quot;: &quot;en_US.UTF-8&quot;,
  &quot;LC_NUMERIC&quot;: &quot;en_US.UTF-8&quot;,
...
    &quot;grouping&quot;: [
      3,
      0
    ]
  },
  &quot;integer&quot;: &quot;123,456,789&quot;,
  &quot;float&quot;: &quot;1,234.5&quot;,
  &quot;test_files&quot;: [
    &quot;&lt;slot-b-source&gt;/Lib/test/test_format.py&quot;,
    &quot;&lt;slot-b-source&gt;/Lib/test/test_types.py&quot;
  ]
}</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><pre><code>CATALOG_RECORD {&quot;kind&quot;: &quot;start&quot;, &quot;case_id&quot;: &quot;issue-4970-case-01&quot;, &quot;selector&quot;: &quot;test.test_format.FormatTest.test_locale&quot;, &quot;interpreter&quot;: &quot;3.11.0alpha (tags/v0.2.0-903-g7a6000d18:7a6000d18, May 13 2023, 02:58:02) \n[rustc 1.67.1]&quot;, &quot;executable&quot;: &quot;&lt;survey&gt;/.build/slot-b/saved/history-7a6000d1/rustpython&quot;, &quot;cwd&quot;: &quot;&lt;survey&gt;/logs/scratch-history-a/7a6000d181&quot;, &quot;selector_derivation&quot;: null, &quot;original_selector&quot;: null, &quot;derivation&quot;: &quot;TODO RustPython skip decorators bypassed in memory; targeted expectedFailure flags cleared&quot;}
CATALOG_RECORD {&quot;kind&quot;: &quot;selection&quot;, &quot;case_id&quot;: &quot;issue-4970-case-01&quot;, &quot;selected_ids&quot;: [&quot;test.test_format.FormatTest.test_locale&quot;], &quot;loader_errors&quot;: [], &quot;module_origin&quot;: &quot;&lt;workspace&gt;/Lib/test/test_format.py&quot;, &quot;module_sha256&quot;: &quot;479f788394653765dad99cc71ecd001059c4638551ddccd872cd47f13b51a9c0&quot;, &quot;bypassed_decorators&quot;: [], &quot;note&quot;: &quot;Import-time bypass records include unselected tests; only selected_ids are executed&quot;}
CATALOG_RECORD {&quot;kind&quot;: &quot;locale_observation&quot;, &quot;arguments&quot;: &quot;(0,)&quot;, &quot;result&quot;: &quot;C&quot;, &quot;localeconv&quot;: {&quot;mon_grouping&quot;: [], &quot;grouping&quot;: [], &quot;int_frac_digits&quot;: 127, &quot;frac_digits&quot;: 127, &quot;p_cs_precedes&quot;: 127, &quot;p_sep_by_space&quot;: 127, &quot;n_cs_precedes&quot;: 127, &quot;p_sign_posn&quot;: 127, &quot;n_sign_posn&quot;: 127, &quot;decimal_point&quot;: &quot;.&quot;, &quot;thousands_sep&quot;: &quot;&quot;, &quot;int_curr_symbol&quot;: &quot;&quot;, &quot;currency_symbol&quot;: &quot;&quot;, &quot;mon_decimal_point&quot;: &quot;&quot;, &quot;mon_thousands_sep&quot;: &quot;&quot;, &quot;n_sep_by_space&quot;: 127, &quot;positive_sign&quot;: &quot;&quot;, &quot;negative_sign&quot;: &quot;&quot;}}
CATALOG_RECORD {&quot;kind&quot;: &quot;locale_observation&quot;, &quot;arguments&quot;: &quot;(0, &#x27;&#x27;)&quot;, &quot;result&quot;: &quot;en_US.UTF-8/C.UTF-8/en_US.UTF-8/en_US.UTF-8/en_US.UTF-8/en_US.UTF-8&quot;, &quot;localeconv&quot;: {&quot;mon_grou</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><pre><code>{
  &quot;LC_ALL_environment&quot;: null,
  &quot;LANG&quot;: &quot;en_US.UTF-8&quot;,
  &quot;LC_NUMERIC&quot;: &quot;en_US.UTF-8&quot;,
...
    &quot;grouping&quot;: [
      3,
      0
    ]
  },
  &quot;integer&quot;: &quot;123,456,789&quot;,
  &quot;float&quot;: &quot;1,234.5&quot;,
  &quot;test_files&quot;: [
    &quot;&lt;slot-b-source&gt;/Lib/test/test_format.py&quot;,
    &quot;&lt;slot-b-source&gt;/Lib/test/test_types.py&quot;
  ]
}</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td></tr>
<tr><th>stderr</th><td valign="top"><pre><code>test_locale (test.test_format.FormatTest.test_locale) ... ok
test_int__format__locale (test.test_types.TypesTests.test_int__format__locale) ... ok
test_float__format__locale (test.test_types.TypesTests.test_float__format__locale) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK</code></pre></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
...
  File &quot;&lt;workspace&gt;/Lib/test/test_format.py&quot;, line 446, in test_locale
    locale.setlocale(locale.LC_ALL, oldloc)
  File &quot;&lt;workspace&gt;/Lib/test/test_format.py&quot;, line 444, in test_locale
    self.assertEqual(text.replace(sep, &#x27;&#x27;), &#x27;1234&#x27; + point + &#x27;5&#x27;)
  File &quot;&lt;workspace&gt;/Lib/test/test_format.py&quot;, line 437, in test_locale
    self.assertIn(sep, text)
AssertionError: &#x27;,&#x27; not found in &#x27;123456789&#x27;

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><pre><code>test_locale (test.test_format.FormatTest.test_locale) ... ok
test_int__format__locale (test.test_types.TypesTests.test_int__format__locale) ... ok
test_float__format__locale (test.test_types.TypesTests.test_float__format__locale) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.005s

OK</code></pre></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-b/saved/current-f39-x86/rustpython -B <additional11-audit>/agent-b/probe-original-locale-tests.py
```

CPython reference command:

```sh
<home>/.local/bin/python3 -B <additional11-audit>/agent-b/probe-original-locale-tests.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

With LC_ALL absent and LANG/LC_NUMERIC=en_US.UTF-8, the unmodified original test_locale and two int/float locale tests pass, with no skip or expectedFailure.

[PR #7350](https://github.com/RustPython/RustPython/pull/7350): use locale grouping, separator and decimal-point data.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The active comma grouping was verified; a C-locale skip is not counted. This narrower bare-n symptom is distinct from the outstanding width/padding issues.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`7a6000d181b7`](https://github.com/RustPython/RustPython/commit/7a6000d181b7611c26f2d1353d0462d7bec26da6), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-catalog-7a6000d181-scratch-actual-locale.stdout](../../evidence/history/logs/issue-4970-case-01/historical-catalog-7a6000d181-scratch-actual-locale.stdout).
- [Full reused historical-catalog-7a6000d181-scratch-actual-locale.stderr](../../evidence/history/logs/issue-4970-case-01/historical-catalog-7a6000d181-scratch-actual-locale.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [locale-original-set-cpython](../../evidence/additional11/agent-b/locale-original-set-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-original-set-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-original-set-cpython.stderr.txt) |
| [locale-original-set-rustpython](../../evidence/additional11/agent-b/locale-original-set-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-original-set-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-original-set-rustpython.stderr.txt) |
| [locale-original-unset-cpython](../../evidence/additional11/agent-b/locale-original-unset-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-original-unset-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-original-unset-cpython.stderr.txt) |
| [locale-original-unset-rustpython](../../evidence/additional11/agent-b/locale-original-unset-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/locale-original-unset-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/locale-original-unset-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
{
  "LC_ALL_environment": null,
  "LANG": "en_US.UTF-8",
  "LC_NUMERIC": "en_US.UTF-8",
  "effective": "en_US.UTF-8",
  "conv": {
    "decimal_point": ".",
    "thousands_sep": ",",
    "grouping": [
      3,
      0
    ]
  },
  "integer": "123,456,789",
  "float": "1,234.5",
  "test_files": [
    "<slot-b-source>/Lib/test/test_format.py",
    "<slot-b-source>/Lib/test/test_types.py"
  ]
}

```

**stderr:**

```text
test_locale (test.test_format.FormatTest.test_locale) ... ok
test_int__format__locale (test.test_types.TypesTests.test_int__format__locale) ... ok
test_float__format__locale (test.test_types.TypesTests.test_float__format__locale) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.005s

OK

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
