# XZ support and the forced lzma skip (#6790)

Original issue: [#6790](https://github.com/RustPython/RustPython/issues/6790)

**Partially resolved — do not close:** The forced skip is gone and basic XZ operations pass. However, identical CPython-generated XZ input returns 0 bytes from the first decompress(max_length=100) call in RustPython, versus 100 bytes in CPython.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-6790-fixed-input.py](../../evidence/initial16/agent-b/probe-6790-fixed-input.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
import lzma

compressed = bytes.fromhex(
    "fd377a585a000004e6d6b4460200210116000000742fe5a3e000ff00265d00291d4a676e62b3eba66db6aa865728962569f10e686905c3e4801a617213ed05b6eb803e0000000000ee4ab9683be553160001428002000000a3072a9ab1c467fb020000000004595a"
)
payload = b"RustPython independent xz probe\n" * 8
d = lzma.LZMADecompressor()
a = d.decompress(compressed, max_length=100)
b = d.decompress(b"", max_length=100)
print("first", len(a), "second", len(b), "needs_input", d.needs_input, "eof", d.eof)
print("first correct", a == payload[:100], "second correct", b == payload[100:200])
```

## Expected and observed results

**Expected:** The original request conditions removal of the forced skip on working XZ support.

**Observed:** The forced skip is gone and basic XZ operations pass. However, identical CPython-generated XZ input returns 0 bytes from the first decompress(max_length=100) call in RustPython, versus 100 bytes in CPython.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
first 0 second 100 needs_input False eof False
first correct False second correct False
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
first 100 second 100 needs_input False eof False
first correct True second correct True
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 0</summary>

**stdout:**

```text
skip True
reason requires lzma
invoked SkipTest
skip_message requires lzma
```

**stderr:**

```text
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-b/saved/current-f39-x86/rustpython' -B -S \
  '<initial16-audit>/agent-b/probe-6790-fixed-input.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B -S \
  '<initial16-audit>/agent-b/probe-6790-fixed-input.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

The forced skip is gone and basic XZ operations pass. However, identical CPython-generated XZ input returns 0 bytes from the first decompress(max_length=100) call in RustPython, versus 100 bytes in CPython.

[PR #7896](https://github.com/RustPython/RustPython/pull/7896): remove the unconditional lzma skip override; [PR #7756](https://github.com/RustPython/RustPython/pull/7756): XZ support.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The corresponding existing test is an expectedFailure, not a pass. Its marker was retained. The remaining concrete streaming defect prevents closure.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/6790/evidence/metadata.json).
- Historical baseline: [`ed785e3d8689`](https://github.com/RustPython/RustPython/commit/ed785e3d868966e2a5f7478632cabd5a630e6934), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/6790/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/6790/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[fixture-6790-cpython](../../evidence/initial16/agent-b/fixture-6790-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fixture-6790-cpython.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fixture-6790-cpython.stderr).
- **[fresh-6790-cp](../../evidence/initial16/agent-b/fresh-6790-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-6790-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-6790-cp.stderr).
- **[fresh-6790-fixed-input-cp](../../evidence/initial16/agent-b/fresh-6790-fixed-input-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-6790-fixed-input-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-6790-fixed-input-cp.stderr).
- **[fresh-6790-fixed-input-rp](../../evidence/initial16/agent-b/fresh-6790-fixed-input-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-6790-fixed-input-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-6790-fixed-input-rp.stderr).
- **[fresh-6790-maxlength-cp](../../evidence/initial16/agent-b/fresh-6790-maxlength-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-6790-maxlength-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-6790-maxlength-cp.stderr).
- **[fresh-6790-maxlength-rp](../../evidence/initial16/agent-b/fresh-6790-maxlength-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-6790-maxlength-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-6790-maxlength-rp.stderr).
- **[fresh-6790-rp](../../evidence/initial16/agent-b/fresh-6790-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-6790-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-6790-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
