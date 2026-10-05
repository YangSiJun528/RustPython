# Ellipsis type name (#8052)

Original issue: [#8052](https://github.com/RustPython/RustPython/issues/8052)

**Verified closure candidate:** The name and repr are `ellipsis` and `<class 'ellipsis'>`; the types alias, JSON error note and existing JSON regression tests also pass.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-8052.py](../../evidence/initial16/agent-b/probe-8052.py.txt). The export preserves the executed code except for documented local-path substitutions.

<details>
<summary>Reproducer code</summary>

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

</details>

## Expected and observed results

**Expected:** The Ellipsis singleton type must use the CPython-visible name ellipsis.

**Observed:** The name and repr are `ellipsis` and `<class 'ellipsis'>`; the types alias, JSON error note and existing JSON regression tests also pass.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
ellipsis
<class 'ellipsis'>
alias True
notes ['when serializing ellipsis object', 'when serializing list item 0', 'when serializing module object', 'when serializing type object']
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
ellipsis
<class 'ellipsis'>
alias True
notes ['when serializing ellipsis object', 'when serializing list item 0', 'when serializing module object', 'when serializing type object']
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 0</summary>

**stdout:**

```text
EllipsisType
<class 'EllipsisType'>
```

**stderr:** No output.

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-b/saved/current-f39-x86/rustpython' -B -S \
  '<initial16-audit>/agent-b/probe-8052.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B -S \
  '<initial16-audit>/agent-b/probe-8052.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

The name and repr are `ellipsis` and `<class 'ellipsis'>`; the types alias, JSON error note and existing JSON regression tests also pass.

[PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** No first-fixing revision was determined.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/8052/evidence/metadata.json).
- Historical baseline: [`83fe92042112`](https://github.com/RustPython/RustPython/commit/83fe92042112f9db89a70495b552ab433d77e751), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/8052/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/8052/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[fresh-8052-cp](../../evidence/initial16/agent-b/fresh-8052-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-8052-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-8052-cp.stderr).
- **[fresh-8052-rp](../../evidence/initial16/agent-b/fresh-8052-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-8052-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-8052-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
