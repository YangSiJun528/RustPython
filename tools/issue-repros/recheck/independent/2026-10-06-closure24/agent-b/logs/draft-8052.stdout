# Ellipsis type name (#8052)

[Original issue](https://github.com/RustPython/RustPython/issues/8052). **Resolved in the reported scope.** The name and repr are `ellipsis` and `<class 'ellipsis'>`; the types alias and all four JSON error notes also match CPython.

## Environment

- Source and standard library: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Verified October 5, 2026 on macOS 26.5.2 ARM64.
- RustPython: 0.6.1, Python 3.14.0.alpha; x86_64 through Rosetta.
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

```sh
export LC_ALL=en_US.UTF-8
```

## Reproducer

Save as `probe-8052.py`.

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

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B -S "$CASE/probe-8052.py"
```

**CPython:**

```sh
"$CP" -B -S "$CASE/probe-8052.py"
```

## Results

**Expected:** The Ellipsis singleton type must use the CPython-visible name ellipsis.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
ellipsis
<class 'ellipsis'>
alias True
notes [
  'when serializing ellipsis object',
  'when serializing list item 0',
  'when serializing module object',
  'when serializing type object',
]
```

The notes list is line-wrapped for readability.

**stderr:**

No output.

### Historical failure

Previously recorded at [`83fe92042112`](https://github.com/RustPython/RustPython/commit/83fe92042112f9db89a70495b552ab433d77e751); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:**

```text
EllipsisType
<class 'EllipsisType'>
```

**stderr:** No output.

## Related change and scope

[PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-b/fresh-8052-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-b/fresh-8052-rp.json).
- [Executed source](../../evidence/initial16/agent-b/probe-8052.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/8052/evidence/metadata.json).

AI assistance: OpenAI Codex.
