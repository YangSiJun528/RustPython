# XZ support and the forced lzma skip (#6790)

[Original issue](https://github.com/RustPython/RustPython/issues/6790). **Partially resolved; keep open.** The forced skip is gone and basic XZ operations pass. However, identical CPython-generated XZ input returns 0 bytes from the first decompress(max_length=100) call in RustPython, versus 100 bytes in CPython.

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

Save as `probe-6790-fixed-input.py`.

```python
import lzma

compressed = bytes.fromhex(
    "fd377a585a000004e6d6b4460200210116000000742fe5a3e000ff00265d0029"
    "1d4a676e62b3eba66db6aa865728962569f10e686905c3e4801a617213ed05b6"
    "eb803e0000000000ee4ab9683be553160001428002000000a3072a9ab1c467fb"
    "020000000004595a"
)
payload = b"RustPython independent xz probe\n" * 8
d = lzma.LZMADecompressor()
a = d.decompress(compressed, max_length=100)
b = d.decompress(b"", max_length=100)
print("first", len(a), "second", len(b), "needs_input", d.needs_input, "eof", d.eof)
print("first correct", a == payload[:100], "second correct", b == payload[100:200])
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B -S "$CASE/probe-6790-fixed-input.py"
```

**CPython:**

```sh
"$CP" -B -S "$CASE/probe-6790-fixed-input.py"
```

## Results

**Expected:** The original request conditions removal of the forced skip on working XZ support.

### RustPython

Exit code: `0`. No timeout.

**stdout:**

```text
first 0 second 100 needs_input False eof False
first correct False second correct False
```

**stderr:**

No output.

### CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
first 100 second 100 needs_input False eof False
first correct True second correct True
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`ed785e3d8689`](https://github.com/RustPython/RustPython/commit/ed785e3d868966e2a5f7478632cabd5a630e6934); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:**

```text
skip True
reason requires lzma
invoked SkipTest
skip_message requires lzma
```

Historical output excerpt; runner metadata and repeated shutdown warnings are omitted.

## Related change and scope

[PR #7896](https://github.com/RustPython/RustPython/pull/7896): remove the unconditional lzma skip override; [PR #7756](https://github.com/RustPython/RustPython/pull/7756): XZ support.

The corresponding existing test is an expectedFailure, not a pass. Its marker was retained. The remaining concrete streaming defect prevents closure.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-b/fresh-6790-fixed-input-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-b/fresh-6790-fixed-input-rp.json).
- [Executed source](../../evidence/initial16/agent-b/probe-6790-fixed-input.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/6790/evidence/metadata.json).

AI assistance: OpenAI Codex.
