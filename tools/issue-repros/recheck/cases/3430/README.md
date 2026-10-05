# ElementTree parsing valid XML (#3430)

Original issue: [#3430](https://github.com/RustPython/RustPython/issues/3430)

**Verified closure candidate:** The original empty root parses successfully. Valid child, text, attribute, namespace and UTF-8 samples agree with CPython.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [3430-original.py](../../evidence/initial16/agent-a/3430-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
import xml.etree.ElementTree as etree

etree.XML("<root></root>")
```

## Expected and observed results

**Expected:** `etree.XML("<root></root>")` must parse valid XML without the None-encoding TypeError.

**Observed:** The original empty root parses successfully. Valid child, text, attribute, namespace and UTF-8 samples agree with CPython.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:** No output.

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:** No output.

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:** No output.

**stderr:**

```text
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
...
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
Traceback (most recent call last):
  File "<survey>/verification-tools/derived-transcripts/issue-3430-case-01/probe.py", line 2, in <module>
    result = etree.XML("<root></root>")
  File "<checkout>/vm/pylib-crate/Lib/xml/etree/ElementTree.py", line 1319, in XML
    parser = XMLParser(target=TreeBuilder())
  File "<checkout>/vm/pylib-crate/Lib/xml/etree/ElementTree.py", line 1508, in __init__
    parser = expat.ParserCreate(encoding, "}")
TypeError: Expected type 'str', not 'NoneType'
```

Excerpt; complete output is in the linked execution record.

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B \
  '<initial16-audit>/agent-a/3430-original.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<initial16-audit>/agent-a/3430-original.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

The original empty root parses successfully. Valid child, text, attribute, namespace and UTF-8 samples agree with CPython.

[PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept None as the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parsing.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** A separate malformed input, `<a></b>`, is still accepted where CPython raises ParseError. That difference prevents a full XML-compatibility claim but does not reproduce the original valid-XML TypeError.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/3430/evidence/metadata.json).
- Historical baseline: [`310578c422c9`](https://github.com/RustPython/RustPython/commit/310578c422c9b3d76eb8c739136b972d78e37180), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/3430/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/3430/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[3430-boundaries-cp](../../evidence/initial16/agent-a/3430-boundaries-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/3430-boundaries-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/3430-boundaries-cp.stderr).
- **[3430-boundaries-rp](../../evidence/initial16/agent-a/3430-boundaries-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/3430-boundaries-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/3430-boundaries-rp.stderr).
- **[3430-original-cp](../../evidence/initial16/agent-a/3430-original-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/3430-original-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/3430-original-cp.stderr).
- **[3430-original-rp](../../evidence/initial16/agent-a/3430-original-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/3430-original-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/3430-original-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
