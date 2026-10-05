# Bool numeric format codes (#4950)

Original issue: [#4950](https://github.com/RustPython/RustPython/issues/4950)

**Verified closure candidate:** False and True match CPython for the original codes, the comment's n/d codes and width/precision controls: 34 recorded results.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Run the shared [probes.py](../../evidence/additional11/agent-a/probes.py.txt) with selector `4950`, as shown in the recorded command. The relevant function is `issue4950`; the full file supplies its imports and dispatcher. The excerpt is formatted for readability.

<details>
<summary>Reproducer function: issue4950</summary>

```python
def issue4950():
    import locale

    locale.setlocale(locale.LC_ALL, "C")
    cases = ["f", "x", "X", "e", "E", "c", "g", "o", "%", "o", "n", "d"]
    cases += ["08x", "+08d", ".2f", ".1%", ">5n"]
    results = []
    for value in (False, True):
        for spec in cases:
            actual = ("{:" + spec + "}").format(value)
            assert actual == format(int(value), spec)
            results.append([value, spec, actual])
    print(
        json.dumps(
            {"locale": locale.setlocale(locale.LC_ALL), "results": results},
            sort_keys=True,
        )
    )
```

</details>

## Expected and observed results

**Expected:** Explicit numeric format codes must format bool through its numeric value.

**Observed:** False and True match CPython for the original codes, the comment's n/d codes and width/precision controls: 34 recorded results.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```json
{
  "locale": "C",
  "results": [
    [
      false,
      "f",
      "0.000000"
    ],
    [
      false,
      "x",
      "0"
    ],
    [
      false,
      "X",
      "0"
    ],
    [
      false,
      "e",
      "0.000000e+00"
    ],
    [
      false,
      "E",
      "0.000000E+00"
    ],
    [
      false,
      "c",
      "\u0000"
    ],
    [
      false,
      "g",
      "0"
    ],
    [
      false,
      "o",
      "0"
    ],
    [
      false,
      "%",
      "0.000000%"
    ],
    [
      false,
      "o",
      "0"
    ],
    [
      false,
      "n",
      "0"
    ],
    [
      false,
      "d",
      "0"
    ],
    [
      false,
      "08x",
      "00000000"
    ],
    [
      false,
      "+08d",
      "+0000000"
    ],
    [
      false,
      ".2f",
      "0.00"
    ],
    [
      false,
      ".1%",
      "0.0%"
    ],
    [
      false,
      ">5n",
      "    0"
    ],
    [
      true,
      "f",
      "1.000000"
    ],
    [
      true,
      "x",
      "1"
    ],
    [
      true,
      "X",
      "1"
    ],
    [
      true,
      "e",
      "1.000000e+00"
    ],
    [
      true,
      "E",
      "1.000000E+00"
    ],
    [
      true,
      "c",
      "\u0001"
    ],
    [
      true,
      "g",
      "1"
    ],
    [
      true,
      "o",
      "1"
    ],
    [
      true,
      "%",
      "100.000000%"
    ],
    [
      true,
      "o",
      "1"
    ],
    [
      true,
      "n",
      "1"
    ],
    [
      true,
      "d",
      "1"
    ],
    [
      true,
      "08x",
      "00000001"
    ],
    [
      true,
      "+08d",
      "+0000001"
    ],
    [
      true,
      ".2f",
      "1.00"
    ],
    [
      true,
      ".1%",
      "100.0%"
    ],
    [
      true,
      ">5n",
      "    1"
    ]
  ]
}
```

JSON whitespace is expanded for readability.

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```json
{
  "locale": "C",
  "results": [
    [
      false,
      "f",
      "0.000000"
    ],
    [
      false,
      "x",
      "0"
    ],
    [
      false,
      "X",
      "0"
    ],
    [
      false,
      "e",
      "0.000000e+00"
    ],
    [
      false,
      "E",
      "0.000000E+00"
    ],
    [
      false,
      "c",
      "\u0000"
    ],
    [
      false,
      "g",
      "0"
    ],
    [
      false,
      "o",
      "0"
    ],
    [
      false,
      "%",
      "0.000000%"
    ],
    [
      false,
      "o",
      "0"
    ],
    [
      false,
      "n",
      "0"
    ],
    [
      false,
      "d",
      "0"
    ],
    [
      false,
      "08x",
      "00000000"
    ],
    [
      false,
      "+08d",
      "+0000000"
    ],
    [
      false,
      ".2f",
      "0.00"
    ],
    [
      false,
      ".1%",
      "0.0%"
    ],
    [
      false,
      ">5n",
      "    0"
    ],
    [
      true,
      "f",
      "1.000000"
    ],
    [
      true,
      "x",
      "1"
    ],
    [
      true,
      "X",
      "1"
    ],
    [
      true,
      "e",
      "1.000000e+00"
    ],
    [
      true,
      "E",
      "1.000000E+00"
    ],
    [
      true,
      "c",
      "\u0001"
    ],
    [
      true,
      "g",
      "1"
    ],
    [
      true,
      "o",
      "1"
    ],
    [
      true,
      "%",
      "100.000000%"
    ],
    [
      true,
      "o",
      "1"
    ],
    [
      true,
      "n",
      "1"
    ],
    [
      true,
      "d",
      "1"
    ],
    [
      true,
      "08x",
      "00000001"
    ],
    [
      true,
      "+08d",
      "+0000001"
    ],
    [
      true,
      ".2f",
      "1.00"
    ],
    [
      true,
      ".1%",
      "100.0%"
    ],
    [
      true,
      ">5n",
      "    1"
    ]
  ]
}
```

JSON whitespace is expanded for readability.

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:** No output.

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
Traceback (most recent call last):
  File "<survey>/repros/4950/issue-4950-case-01/source-01.py", line 1, in <module>
    '{:f}'.format(False)
ValueError: Invalid format specifier
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B '<additional11-audit>/agent-a/probes.py' \
  4950
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<additional11-audit>/agent-a/probes.py' 4950
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

False and True match CPython for the original codes, the comment's n/d codes and width/precision controls: 34 recorded results.

[PR #5012](https://github.com/RustPython/RustPython/pull/5012): update the parser/format dependency · [Parser PR #91](https://github.com/RustPython/Parser/pull/91).

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** Locale was C for this issue. The broader locale defects in #4613 and #5181 are separate.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`fa790558211e`](https://github.com/RustPython/RustPython/commit/fa790558211ec690541299258f44d7453501958a), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-fa79055821-01-75703bc4-6d760217.stdout](../../evidence/history/logs/issue-4950-case-01/historical-fa79055821-01-75703bc4-6d760217.stdout).
- [Full reused historical-fa79055821-01-75703bc4-6d760217.stderr](../../evidence/history/logs/issue-4950-case-01/historical-fa79055821-01-75703bc4-6d760217.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

- **[4950-cpython](../../evidence/additional11/agent-a/4950-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4950-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4950-cpython.stderr.txt).
- **[4950-rustpython](../../evidence/additional11/agent-a/4950-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4950-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4950-rustpython.stderr.txt).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
