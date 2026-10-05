# SymPy import with the reported versions (#4506)

Original issue: [#4506](https://github.com/RustPython/RustPython/issues/4506)

**Verified closure candidate:** SymPy 1.11.1 with mpmath 1.2.1 imports successfully. Tracing observes the original power.py:378 is_commutative assignment, and the reported Pow path succeeds.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-sympy-original.py](../../evidence/additional11/agent-b/probe-sympy-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

<details>
<summary>Reproducer code</summary>

```python
import sys
import json

site = "<survey>/verification-tools/package-history-4506-original/site"
sys.path.insert(0, site)
import sympy
import mpmath
from sympy import Pow, S, Symbol, expand
from sympy.core.cache import clear_cache

assert sympy.__version__ == "1.11.1"
assert mpmath.__version__ == "1.2.1"
assert sympy.__file__.startswith(site + "/")
assert mpmath.__file__.startswith(site + "/")
clear_cache()
events = []


def trace(frame, event, arg):
    if (
        event == "line"
        and frame.f_code.co_filename == site + "/sympy/core/power.py"
        and frame.f_lineno == 378
    ):
        events.append([frame.f_code.co_name, frame.f_lineno])
    return trace


sys.settrace(trace)
value = Pow(S.Exp1, -1, evaluate=False)
sys.settrace(None)
assert value.is_commutative is True
assert events, "Original power.py assignment was not observed"
x = Symbol("x")
assert expand((x + 1) ** 2) == x**2 + 2 * x + 1
print(
    json.dumps(
        {
            "versions": [sympy.__version__, mpmath.__version__],
            "files": [sympy.__file__, mpmath.__file__],
            "original_assignment": events,
            "pow": str(value),
            "is_commutative": value.is_commutative,
            "expanded": str(expand((x + 1) ** 2)),
        },
        indent=2,
    )
)
```

</details>

## Expected and observed results

**Expected:** The already installed reported package versions must import without the descriptor AttributeError.

**Observed:** SymPy 1.11.1 with mpmath 1.2.1 imports successfully. Tracing observes the original power.py:378 is_commutative assignment, and the reported Pow path succeeds.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
{
  "versions": [
    "1.11.1",
    "1.2.1"
...
    "<survey>/verification-tools/package-history-4506-original/site/mpmath/__init__.py"
  ],
  "original_assignment": [
    [
      "__new__",
      378
    ]
  ],
  "pow": "1/E",
  "is_commutative": true,
  "expanded": "x**2 + 2*x + 1"
}
```

Excerpt; complete output is in the linked execution record.

**stderr:**

```text
<survey>/verification-tools/package-history-4506-original/site/sympy/testing/runtests.py:275: SyntaxWarning: 'return' in a 'finally' block
  return p.returncode
```

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
{
  "versions": [
    "1.11.1",
    "1.2.1"
...
    "<survey>/verification-tools/package-history-4506-original/site/mpmath/__init__.py"
  ],
  "original_assignment": [
    [
      "__new__",
      378
    ]
  ],
  "pow": "1/E",
  "is_commutative": true,
  "expanded": "x**2 + 2*x + 1"
}
```

Excerpt; complete output is in the linked execution record.

**stderr:**

```text
<survey>/verification-tools/package-history-4506-original/site/sympy/testing/runtests.py:275: SyntaxWarning: 'return' in a 'finally' block
  return p.returncode
```

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
...
    class LambertW(Function):
  File "<survey>/verification-tools/package-history-4506-original/site/sympy/functions/elementary/exponential.py", line 1159, in LambertW
    _singularities = (-Pow(S.Exp1, -1, evaluate=False), S.ComplexInfinity)
  File "<survey>/verification-tools/package-history-4506-original/site/sympy/core/cache.py", line 74, in wrapper
    retval = func(*args, **kwargs)
  File "<survey>/verification-tools/package-history-4506-original/site/sympy/core/cache.py", line 70, in wrapper
    retval = cfunc(*args, **kwargs)
  File "<slot-b-source>/pylib/Lib/functools.py", line 593, in wrapper
    result = user_function(*args, **kwds)
  File "<survey>/verification-tools/package-history-4506-original/site/sympy/core/power.py", line 378, in __new__
    obj.is_commutative = (b.is_commutative and e.is_commutative)
AttributeError: can't set attribute
```

Excerpt; complete output is in the linked execution record.

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-b/saved/current-f39-x86/rustpython' -B \
  '<additional11-audit>/agent-b/probe-sympy-original.py'
```

CPython reference command:

```sh
'<home>/.local/bin/python3' -B '<additional11-audit>/agent-b/probe-sympy-original.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

SymPy 1.11.1 with mpmath 1.2.1 imports successfully. Tracing observes the original power.py:378 is_commutative assignment, and the reported Pow path succeeds.

[PR #6390](https://github.com/RustPython/RustPython/pull/6390): install declared slot descriptors even over inherited attributes.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The same dependency files were used in RustPython and CPython and their RECORD hashes were checked. Package installation and the full SymPy suite were not rerun.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`adc23253e4b5`](https://github.com/RustPython/RustPython/commit/adc23253e4b58980b407ba2760dbe61681d752fc), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-pinned-sympy111-mpmath121-b.stdout](../../evidence/history/logs/issue-4506-case-01/historical-pinned-sympy111-mpmath121-b.stdout).
- [Full reused historical-pinned-sympy111-mpmath121-b.stderr](../../evidence/history/logs/issue-4506-case-01/historical-pinned-sympy111-mpmath121-b.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

- **[4506-cpython](../../evidence/additional11/agent-b/4506-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/4506-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/4506-cpython.stderr.txt).
- **[4506-rustpython](../../evidence/additional11/agent-b/4506-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/4506-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/4506-rustpython.stderr.txt).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
