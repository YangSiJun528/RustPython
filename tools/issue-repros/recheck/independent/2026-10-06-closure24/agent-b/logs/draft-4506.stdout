# SymPy import with the reported versions (#4506)

[Original issue](https://github.com/RustPython/RustPython/issues/4506). **Resolved in the reported scope.** SymPy 1.11.1 with mpmath 1.2.1 imports successfully. Tracing observes the original power.py:378 is_commutative assignment, and the reported Pow path succeeds.

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
export LANG=en_US.UTF-8 LC_NUMERIC=en_US.UTF-8
```

`LC_ALL` was unset in these recorded runs.

```sh
unset LC_ALL
```

Dependencies: **SymPy 1.11.1** and **mpmath 1.2.1**. Set `SYMPY_SITE` to their shared package directory and export it. Both interpreters used the same package files; package installation and the full SymPy suite are outside this check.

```sh
export SYMPY_SITE
```

## Reproducer

Save as `probe-sympy-original.py`. `SYMPY_SITE` replaces the recorded package path.

```python
import sys
import os
import json

site = os.environ["SYMPY_SITE"]
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

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probe-sympy-original.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/probe-sympy-original.py"
```

## Results

**Expected:** The already installed reported package versions must import without the descriptor AttributeError.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```json
{
  "versions": [
    "1.11.1",
    "1.2.1"
  ],
  "files": [
    "$SYMPY_SITE/sympy/__init__.py",
    "$SYMPY_SITE/mpmath/__init__.py"
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

**stderr:**

```text
$SYMPY_SITE/sympy/testing/runtests.py:275: SyntaxWarning: 'return' in a 'finally' block
  return p.returncode
```

### Historical failure

Previously recorded at [`adc23253e4b5`](https://github.com/RustPython/RustPython/commit/adc23253e4b58980b407ba2760dbe61681d752fc); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

**stderr:**

```text
    class LambertW(Function):
  File "$SYMPY_SITE/sympy/functions/elementary/exponential.py", line 1159, in LambertW
    _singularities = (-Pow(S.Exp1, -1, evaluate=False), S.ComplexInfinity)
  File "$SYMPY_SITE/sympy/core/cache.py", line 74, in wrapper
    retval = func(*args, **kwargs)
  File "$SYMPY_SITE/sympy/core/cache.py", line 70, in wrapper
    retval = cfunc(*args, **kwargs)
  File "$SRC/pylib/Lib/functools.py", line 593, in wrapper
    result = user_function(*args, **kwds)
  File "$SYMPY_SITE/sympy/core/power.py", line 378, in __new__
    obj.is_commutative = (b.is_commutative and e.is_commutative)
AttributeError: can't set attribute
```

## Related change and scope

[PR #6390](https://github.com/RustPython/RustPython/pull/6390): install declared slot descriptors even over inherited attributes.

The same dependency files were used in RustPython and CPython and their RECORD hashes were checked. Package installation and the full SymPy suite were not rerun.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-b/4506-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-b/4506-rustpython.json).
- [Executed source](../../evidence/additional11/agent-b/probe-sympy-original.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
