# Locale support for FormatSpec n (#4613)

Original issue: [#4613](https://github.com/RustPython/RustPython/issues/4613)

**Partially resolved — do not close:** Basic n and the original locale tests pass. Across five available locales, 395 formatting results include 102 differences: 84 zero-padding cases and 18 other Unicode-separator width cases.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-locale-unicode-width.py](../../evidence/additional11/agent-b/probe-locale-unicode-width.py.txt). The export preserves the executed code except for documented local-path substitutions.

<details>
<summary>Reproducer code</summary>

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

</details>

## Expected and observed results

**Expected:** Locale-sensitive n formatting must preserve grouping and character-based field width.

**Observed:** Basic n and the original locale tests pass. Across five available locales, 395 formatting results include 102 differences: 84 zero-padding cases and 18 other Unicode-separator width cases.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 1</summary>

**stdout:**

```text
{
  "locale": "fr_FR.UTF-8",
  "conv": {
    "decimal_point": ",",
...
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

Excerpt; complete output is in the linked execution record.

**stderr:**

```text
Traceback (most recent call last):
  File "<additional11-audit>/agent-b/probe-locale-unicode-width.py", line 12, in <module>
    assert len(padded) == 20, 'Locale separator must count as one character in field width'
           ^^^^^^^^^^^^^^^^^
AssertionError: Locale separator must count as one character in field width
```

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
{
  "locale": "fr_FR.UTF-8",
  "conv": {
    "decimal_point": ",",
...
    "grouping": [
      3,
      0
    ]
  },
  "plain": "1\u202f234",
  "plain_characters": 5,
  "plain_bytes": 7,
  "padded": "               1\u202f234",
  "padded_characters": 20,
  "padded_bytes": 22
}
```

Excerpt; complete output is in the linked execution record.

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:**

```text
CATALOG_RECORD {"kind": "start", "case_id": "issue-4613-case-01", "selector": "test.test_types.TypesTests.{test_float__format__locale,test_int__format__locale}", "interpreter": "3.11.0alpha (tags/v0.2.0-311-ga7c985685:a7c985685, Mar  2 2023, 15:34:45) \n[rustc 1.67.1]", "executable": "<survey>/.build/slot-a/release/rustpython", "cwd": "<survey>/logs/scratch-history-a/a7c9856851", "selector_derivation": "Exact locale n-format tests referenced through issue4613/PR4609, now lines433\u2013448. Run with en_US.UTF-8 installed and LC_ALL unset; retain run_with_locale wrapper. Log actual locale so fallback C locale cannot masquerade as locale-grouping proof.", "original_selector": null, "derivation": "TODO RustPython skip decorators bypassed in memory; targeted expectedFailure flags cleared"}
CATALOG_RECORD {"kind": "selection", "case_id": "issue-4613-case-01", "selected_ids": ["test.test_types.TypesTests.test_float__format__locale", "test.test_types.TypesTests.test_int__format__locale"], "loader_errors": [], "module_origin": "<workspace>/pylib/Lib/test/test_types.py", "module_sha256": "18f8783da5a0ce95f3dda32f99829f506161a11a3e11c035a6bbdaac02fe19ed", "bypassed_decorators": [{"kind": "skip", "object": "test.test_types.TypesTests.test_int__format__locale", "reason": "TODO: RustPython format code n is not integrated with locale", "action": "decoration-time identity; original body and other decorators retained"}, {"kind": "expectedFailure_preserved", "object": "test.test_types.TypesTests.test_float__format__locale", "action": "No explicit RustPython marker in declaration prefix; pres
```

Excerpt; complete output is in the linked execution record.

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
test_float__format__locale (test.test_types.TypesTests.test_float__format__locale) ... expected failure
test_int__format__locale (test.test_types.TypesTests.test_int__format__locale) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.004s

OK (expected failures=1)
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-b/saved/current-f39-x86/rustpython' -B \
  '<additional11-audit>/agent-b/probe-locale-unicode-width.py'
```

CPython reference command:

```sh
'<home>/.local/bin/python3' -B '<additional11-audit>/agent-b/probe-locale-unicode-width.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

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

<details>
<summary>Execution records (12 runs)</summary>

- **[4613-cross-cpython](../../evidence/additional11/agent-a/4613-cross-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4613-cross-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4613-cross-cpython.stderr.txt).
- **[4613-cross-rustpython](../../evidence/additional11/agent-a/4613-cross-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4613-cross-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4613-cross-rustpython.stderr.txt).
- **[4613-unicode-width-cpython](../../evidence/additional11/agent-b/4613-unicode-width-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/4613-unicode-width-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/4613-unicode-width-cpython.stderr.txt).
- **[4613-unicode-width-rustpython](../../evidence/additional11/agent-b/4613-unicode-width-rustpython.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/4613-unicode-width-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/4613-unicode-width-rustpython.stderr.txt).
- **[4613-zero-padding-cpython](../../evidence/additional11/agent-b/4613-zero-padding-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/4613-zero-padding-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/4613-zero-padding-cpython.stderr.txt).
- **[4613-zero-padding-rustpython](../../evidence/additional11/agent-b/4613-zero-padding-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/4613-zero-padding-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/4613-zero-padding-rustpython.stderr.txt).
- **[locale-matrix-cpython](../../evidence/additional11/agent-b/locale-matrix-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/locale-matrix-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/locale-matrix-cpython.stderr.txt).
- **[locale-matrix-rustpython](../../evidence/additional11/agent-b/locale-matrix-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/locale-matrix-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/locale-matrix-rustpython.stderr.txt).
- **[locale-original-set-cpython](../../evidence/additional11/agent-b/locale-original-set-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/locale-original-set-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/locale-original-set-cpython.stderr.txt).
- **[locale-original-set-rustpython](../../evidence/additional11/agent-b/locale-original-set-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/locale-original-set-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/locale-original-set-rustpython.stderr.txt).
- **[locale-original-unset-cpython](../../evidence/additional11/agent-b/locale-original-unset-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/locale-original-unset-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/locale-original-unset-cpython.stderr.txt).
- **[locale-original-unset-rustpython](../../evidence/additional11/agent-b/locale-original-unset-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/locale-original-unset-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/locale-original-unset-rustpython.stderr.txt).

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
