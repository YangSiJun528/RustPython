# Native class-method descriptor type (#4690)

Original issue: [#4690](https://github.com/RustPython/RustPython/issues/4690)

**Verified closure candidate:** Both original descriptor queries return classmethod_descriptor. Binding and representative additional native descriptors agree with CPython.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [4690-original.py](../../evidence/initial16/agent-a/4690-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
print(type(dict.__dict__["fromkeys"]))
print(type(dict.fromkeys))
```

## Expected and observed results

**Expected:** Native class methods must use the classmethod_descriptor type.

**Observed:** Both original descriptor queries return classmethod_descriptor. Binding and representative additional native descriptors agree with CPython.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
<class 'classmethod_descriptor'>
<class 'builtin_function_or_method'>
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
<class 'classmethod_descriptor'>
<class 'builtin_function_or_method'>
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 0</summary>

**stdout:**

```text
classmethod
method
```

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B \
  '<initial16-audit>/agent-a/4690-original.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<initial16-audit>/agent-a/4690-original.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

Both original descriptor queries return classmethod_descriptor. Binding and representative additional native descriptors agree with CPython.

[PR #8780](https://github.com/RustPython/RustPython/pull/8780): native OrderedDict and class-method descriptors.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** No claim is made about every descriptor or every introspection API.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4690/evidence/metadata.json).
- Historical baseline: [`8ff947e83a65`](https://github.com/RustPython/RustPython/commit/8ff947e83a65b74c920edc63aed8a0a5854b8612), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/4690/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/4690/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[4690-boundaries-cp](../../evidence/initial16/agent-a/4690-boundaries-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4690-boundaries-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4690-boundaries-cp.stderr).
- **[4690-boundaries-rp](../../evidence/initial16/agent-a/4690-boundaries-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4690-boundaries-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4690-boundaries-rp.stderr).
- **[4690-original-cp](../../evidence/initial16/agent-a/4690-original-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4690-original-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4690-original-cp.stderr).
- **[4690-original-rp](../../evidence/initial16/agent-a/4690-original-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-a/4690-original-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-a/4690-original-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
