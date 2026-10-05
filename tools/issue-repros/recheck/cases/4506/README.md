# #4506 — SymPy import with the reported versions

Original issue: [#4506](https://github.com/RustPython/RustPython/issues/4506)

**Verified closure candidate:** SymPy 1.11.1 with mpmath 1.2.1 imports successfully. Tracing observes the original power.py:378 is_commutative assignment, and the reported Pow path succeeds.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-sympy-original.py](../../evidence/additional11/agent-b/probe-sympy-original.py.txt). The export preserves the executed code except for documented local-path substitutions.

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

## Expected and observed results

**Expected:** The already installed reported package versions must import without the descriptor AttributeError.

**Observed:** SymPy 1.11.1 with mpmath 1.2.1 imports successfully. Tracing observes the original power.py:378 is_commutative assignment, and the reported Pow path succeeds.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>{
  &quot;versions&quot;: [
    &quot;1.11.1&quot;,
    &quot;1.2.1&quot;
...
    &quot;&lt;survey&gt;/verification-tools/package-history-4506-original/site/mpmath/__init__.py&quot;
  ],
  &quot;original_assignment&quot;: [
    [
      &quot;__new__&quot;,
      378
    ]
  ],
  &quot;pow&quot;: &quot;1/E&quot;,
  &quot;is_commutative&quot;: true,
  &quot;expanded&quot;: &quot;x**2 + 2*x + 1&quot;
}</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><em>No output</em></td><td valign="top"><pre><code>{
  &quot;versions&quot;: [
    &quot;1.11.1&quot;,
    &quot;1.2.1&quot;
...
    &quot;&lt;survey&gt;/verification-tools/package-history-4506-original/site/mpmath/__init__.py&quot;
  ],
  &quot;original_assignment&quot;: [
    [
      &quot;__new__&quot;,
      378
    ]
  ],
  &quot;pow&quot;: &quot;1/E&quot;,
  &quot;is_commutative&quot;: true,
  &quot;expanded&quot;: &quot;x**2 + 2*x + 1&quot;
}</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td></tr>
<tr><th>stderr</th><td valign="top"><pre><code>&lt;survey&gt;/verification-tools/package-history-4506-original/site/sympy/testing/runtests.py:275: SyntaxWarning: &#x27;return&#x27; in a &#x27;finally&#x27; block
  return p.returncode</code></pre></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
...
    class LambertW(Function):
  File &quot;&lt;survey&gt;/verification-tools/package-history-4506-original/site/sympy/functions/elementary/exponential.py&quot;, line 1159, in LambertW
    _singularities = (-Pow(S.Exp1, -1, evaluate=False), S.ComplexInfinity)
  File &quot;&lt;survey&gt;/verification-tools/package-history-4506-original/site/sympy/core/cache.py&quot;, line 74, in wrapper
    retval = func(*args, **kwargs)
  File &quot;&lt;survey&gt;/verification-tools/package-history-4506-original/site/sympy/core/cache.py&quot;, line 70, in wrapper
    retval = cfunc(*args, **kwargs)
  File &quot;&lt;slot-b-source&gt;/pylib/Lib/functools.py&quot;, line 593, in wrapper
    result = user_function(*args, **kwds)
  File &quot;&lt;survey&gt;/verification-tools/package-history-4506-original/site/sympy/core/power.py&quot;, line 378, in __new__
    obj.is_commutative = (b.is_commutative and e.is_commutative)
AttributeError: can&#x27;t set attribute</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><pre><code>&lt;survey&gt;/verification-tools/package-history-4506-original/site/sympy/testing/runtests.py:275: SyntaxWarning: &#x27;return&#x27; in a &#x27;finally&#x27; block
  return p.returncode</code></pre></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-b/saved/current-f39-x86/rustpython -B <additional11-audit>/agent-b/probe-sympy-original.py
```

CPython reference command:

```sh
<home>/.local/bin/python3 -B <additional11-audit>/agent-b/probe-sympy-original.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

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

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [4506-cpython](../../evidence/additional11/agent-b/4506-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/4506-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/4506-cpython.stderr.txt) |
| [4506-rustpython](../../evidence/additional11/agent-b/4506-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/4506-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/4506-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
{
  "versions": [
    "1.11.1",
    "1.2.1"
  ],
  "files": [
    "<survey>/verification-tools/package-history-4506-original/site/sympy/__init__.py",
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

**stderr:**

```text
<survey>/verification-tools/package-history-4506-original/site/sympy/testing/runtests.py:275: SyntaxWarning: 'return' in a 'finally' block
  return p.returncode

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
