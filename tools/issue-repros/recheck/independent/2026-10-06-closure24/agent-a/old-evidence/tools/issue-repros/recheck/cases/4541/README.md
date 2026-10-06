# Safe path flags and path insertion (#4541)

[Original issue](https://github.com/RustPython/RustPython/issues/4541). **Resolved in the reported scope.** `-P` and `PYTHONSAFEPATH` control actual automatic path insertion, including script, command, module and interactive execution.

## Environment and fixtures

- Source and standard library: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Verified October 5, 2026 on macOS 26.5.2 ARM64.
- RustPython 0.6.1 / Python 3.14.0.alpha and CPython 3.14.6, both ARM64.

Use absolute paths: set `RP` and `CP` to those executables and `SRC` to the matching RustPython source directory. Put the two files below in `$SRC/repro_fixture` and set `CASE` to that directory. The fixture directory name and absolute paths are shortened from the recorded inputs; the import checks and flags are unchanged.

```sh
CASE="$SRC/repro_fixture"
export RP CP SRC CASE
unset PYTHONPATH PYTHONHOME PYTHONWARNINGS PYTHONSTARTUP PYTHONSAFEPATH
export PYTHONDONTWRITEBYTECODE=1 LANG=C LC_ALL=C NO_COLOR=1 TERM=dumb
cd "$SRC"
```

### safe_fixture.py

```python
value = "new-safe-path-fixture"
```

### safe_report.py

```python
import sys
import os
import json
import importlib


def can_import(name):
    try:
        m = importlib.import_module(name)
        return m.value
    except ModuleNotFoundError:
        return False


print(
    json.dumps(
        {
            "safe_path": sys.flags.safe_path,
            "isolated": sys.flags.isolated,
            "path": sys.path,
            "cwd": os.getcwd(),
            "bare_import": can_import("safe_fixture"),
            "cwd_import": can_import("repro_fixture.safe_fixture"),
        },
        sort_keys=True,
    )
)
```

## Run

For the command-mode comparison:

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B -c "$(cat "$CASE/safe_report.py")"
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B -P -c "$(cat "$CASE/safe_report.py")"

"$CP" -B -c "$(cat "$CASE/safe_report.py")"
"$CP" -B -P -c "$(cat "$CASE/safe_report.py")"
```

The same recorded checks covered these invocation forms:

- **Script:** replace `-c "$(cat "$CASE/safe_report.py")"` with `"$CASE/safe_report.py"`. The default prepends the script directory; `-P` suppresses that entry.
- **Symlink:** run a symlink to `safe_report.py`, with and without `-P`. The default entry resolves to the real script directory.
- **Module:** use `-m safe_report`. Set `RUSTPYTHONPATH="$SRC/Lib:$CASE"` for RustPython and `PYTHONPATH="$CASE"` for CPython so the module remains explicitly discoverable with `-P`.
- **Environment flag:** omit `-P` and set `PYTHONSAFEPATH=1`. An empty value leaves safe-path mode disabled; any nonempty value, including `0`, enables it.
- **Environment controls:** `-E` ignores `PYTHONSAFEPATH` and explicit module-search environment variables. `-I` enables safe-path behavior and also ignores those variables.

For the interactive check, launch `"$RP" -B -q` with `RUSTPYTHONPATH="$SRC/Lib"`, and separately `"$CP" -B -q`. Repeat with `-P` or `PYTHONSAFEPATH=1`. Enter the following in the actual terminal session:

```text
import sys, os, json
print("REPL_RESULT=" + json.dumps({
    "safe_path": sys.flags.safe_path,
    "path": sys.path,
    "cwd": os.getcwd(),
}), flush=True)
os._exit(0)
```

`TERM=dumb` selected the basic REPL in both interpreters. Its fallback warning is expected; stdout and stderr are merged in the PTY transcript.

## Expected and observed results

Both interpreters produced the following flag and fixture-import results in command mode:

```text
default:
  safe_path = False
  isolated = 0
  path begins with ""
  bare_import = False
  cwd_import = "new-safe-path-fixture"

-P:
  safe_path = True
  isolated = 0
  path has no automatically inserted ""
  bare_import = False
  cwd_import = False
```

Each command-mode run exited `0` with empty stderr. Interpreter-specific standard-library entries differ, so the complete `sys.path` lists are not expected to be identical.

Script, symlink and PTY runs confirmed the same suppression of their automatic unsafe entries. Explicit entries supplied through `RUSTPYTHONPATH` or `PYTHONPATH` remained searchable under `-P`, including the module-mode fixture.

The 52 recorded processes had no timeouts. The four module-mode `-E`/`-I` runs exited `1` because they ignored the only explicit path to `safe_report`; those lookup failures are expected. The remaining runs exited `0`.

### Historical failure

At [`746cb0493f73`](https://github.com/RustPython/RustPython/commit/746cb0493f7371304ceafec88c56e5de59155b95), the previously recorded command rejected `-P` and exited `1`:

```text
error: Found argument '-P' which wasn't expected, or isn't valid in this context
```

## Related changes

- [PR #4611](https://github.com/RustPython/RustPython/pull/4611): connect `-P`, the environment and `safe_path`.
- [PR #5049](https://github.com/RustPython/RustPython/pull/5049): make automatic insertion conditional on `safe_path`.
- [PR #8605](https://github.com/RustPython/RustPython/pull/8605): resolve script paths for insertion.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- RustPython [default](../../evidence/additional11/agent-a/4541-rustpython-command-default.json) and [`-P`](../../evidence/additional11/agent-a/4541-rustpython-command-P.json).
- CPython [default](../../evidence/additional11/agent-a/4541-cpython-command-default.json) and [`-P`](../../evidence/additional11/agent-a/4541-cpython-command-P.json).
- [Recorded fixture](../../evidence/additional11/agent-a/safe_fixture.py.txt) and [recorded probe](../../evidence/additional11/agent-a/safe_report.py.txt).
- [All modes, environments and results](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
