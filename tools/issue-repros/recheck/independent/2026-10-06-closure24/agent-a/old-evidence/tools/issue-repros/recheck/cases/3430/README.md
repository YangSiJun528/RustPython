# ElementTree parsing valid XML (#3430)

[Original issue](https://github.com/RustPython/RustPython/issues/3430). **Resolved in the reported scope.** The original empty root parses successfully. Valid child, text, attribute, namespace and UTF-8 samples agree with CPython.

## Environment

- Source and standard library: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Verified October 5, 2026 on macOS 26.5.2 ARM64.
- RustPython: 0.6.1, Python 3.14.0.alpha; native ARM64.
- Comparison: CPython 3.14.6 ARM64.

Use absolute paths for the variables below:

- `RP`: the RustPython executable for this commit.
- `CP`: the CPython 3.14.6 executable.
- `SRC`: the source directory at this commit, including its matching `Lib`.
- `CASE`: the directory containing the files shown below.

Shell variables replace recorded absolute paths. Export them so the Python inputs can use them:

```sh
export RP CP SRC CASE
unset PYTHONPATH PYTHONHOME PYTHONWARNINGS PYTHONSTARTUP
export PYTHONDONTWRITEBYTECODE=1
```

## Reproducer

Save as `3430-original.py`.

```python
import xml.etree.ElementTree as etree

etree.XML("<root></root>")
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/3430-original.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/3430-original.py"
```

## Results

**Expected:** `etree.XML("<root></root>")` must parse valid XML without the None-encoding TypeError.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

No output.

**stderr:**

No output.

### Historical failure

Previously recorded at [`310578c422c9`](https://github.com/RustPython/RustPython/commit/310578c422c9b3d76eb8c739136b972d78e37180); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

**stderr:**

```text
Traceback (most recent call last):
  File "<survey>/verification-tools/derived-transcripts/issue-3430-case-01/probe.py", line 2, in <module>
    result = etree.XML("<root></root>")
  File "<checkout>/vm/pylib-crate/Lib/xml/etree/ElementTree.py", line 1319, in XML
    parser = XMLParser(target=TreeBuilder())
  File "<checkout>/vm/pylib-crate/Lib/xml/etree/ElementTree.py", line 1508, in __init__
    parser = expat.ParserCreate(encoding, "}")
TypeError: Expected type 'str', not 'NoneType'
```

## Related change and scope

[PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept None as the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parsing.

A separate malformed input, `<a></b>`, is still accepted where CPython raises ParseError. That difference prevents a full XML-compatibility claim but does not reproduce the original valid-XML TypeError.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-a/3430-original-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-a/3430-original-rp.json).
- [Executed source](../../evidence/initial16/agent-a/3430-original.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/3430/evidence/metadata.json).

AI assistance: OpenAI Codex.
