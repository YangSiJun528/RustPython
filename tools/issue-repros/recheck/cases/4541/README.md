# Safe path flags and path insertion (#4541)

Original issue: [#4541](https://github.com/RustPython/RustPython/issues/4541)

**Verified closure candidate:** Script, -c, -m, symlink and actual PTY REPL checks confirm -P and PYTHONSAFEPATH suppress automatic unsafe paths; environment, -E and -I controls agree with CPython.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

This checks actual path insertion and fixture imports for scripts, `-c`, `-m`, symlinks and an actual PTY REPL. The recorded runs compare the default behavior, `-P`, `PYTHONSAFEPATH`, `-E` and `-I`.

The representative `-P -c` run below must report `safe_path: true`, omit the automatic empty path entry and fail to import the local fixture through that entry. The [RustPython record](../../evidence/additional11/agent-a/4541-rustpython-command-P.json) and [CPython record](../../evidence/additional11/agent-a/4541-cpython-command-P.json) preserve the exact input and environment.

<details>
<summary>Python input passed to -c (formatted for display)</summary>

```python
import sys, os, json, importlib


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
            "cwd_import": can_import(
                "independent-verification.2026-10-05-additional11-f39b054.agent-a.safe_fixture"
            ),
        },
        sort_keys=True,
    )
)
```

</details>

## Expected and observed results

**Expected:** sys.flags.safe_path, -P and nonempty PYTHONSAFEPATH must control actual automatic sys.path insertion.

**Observed:** Script, -c, -m, symlink and actual PTY REPL checks confirm -P and PYTHONSAFEPATH suppress automatic unsafe paths; environment, -E and -I controls agree with CPython.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

Representative `-P -c` run: [execution record](../../evidence/additional11/agent-a/4541-rustpython-command-P.json).

**stdout:**

```json
{
  "bare_import": false,
  "cwd": "<workspace>",
  "cwd_import": false,
  "isolated": 0,
  "path": [
    "<workspace>/Lib",
    "<workspace>/lib/python314.zip",
    "<workspace>/lib/python3.14",
    "<workspace>/lib/python3.14/lib-dynload"
  ],
  "safe_path": true
}
```

JSON whitespace is expanded for readability.

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

Representative `-P -c` run: [execution record](../../evidence/additional11/agent-a/4541-cpython-command-P.json).

**stdout:**

```json
{
  "bare_import": false,
  "cwd": "<workspace>",
  "cwd_import": false,
  "isolated": 0,
  "path": [
    "<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/lib/python314.zip",
    "<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/lib/python3.14",
    "<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/lib/python3.14/lib-dynload",
    "<home>/.local/lib/python3.14/site-packages",
    "<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/lib/python3.14/site-packages"
  ],
  "safe_path": true
}
```

JSON whitespace is expanded for readability.

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:** No output.

**stderr:**

```text
error: Found argument '-P' which wasn't expected, or isn't valid in this context

USAGE:
    rustpython [OPTIONS] [-c CMD | -m MODULE | FILE] [PYARGS]...

For more information try --help
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

<details>
<summary>Recorded shell command</summary>

```sh
<survey>/.build/slot-a/verification/rustpython -B -P -c 'import sys, os, json, importlib
def can_import(name):
    try:
        m=importlib.import_module(name)
        return m.value
    except ModuleNotFoundError:
        return False
print(json.dumps({'"'"'safe_path'"'"':sys.flags.safe_path,'"'"'isolated'"'"':sys.flags.isolated,'"'"'path'"'"':sys.path,'"'"'cwd'"'"':os.getcwd(),'"'"'bare_import'"'"':can_import('"'"'safe_fixture'"'"'),'"'"'cwd_import'"'"':can_import('"'"'independent-verification.2026-10-05-additional11-f39b054.agent-a.safe_fixture'"'"')},sort_keys=True))
'
```

</details>

CPython reference command:

<details>
<summary>Recorded shell command</summary>

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B -P -c 'import sys, os, json, importlib
def can_import(name):
    try:
        m=importlib.import_module(name)
        return m.value
    except ModuleNotFoundError:
        return False
print(json.dumps({'"'"'safe_path'"'"':sys.flags.safe_path,'"'"'isolated'"'"':sys.flags.isolated,'"'"'path'"'"':sys.path,'"'"'cwd'"'"':os.getcwd(),'"'"'bare_import'"'"':can_import('"'"'safe_fixture'"'"'),'"'"'cwd_import'"'"':can_import('"'"'independent-verification.2026-10-05-additional11-f39b054.agent-a.safe_fixture'"'"')},sort_keys=True))
'
```

</details>

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY records, stdout and stderr are merged in the terminal transcript; replay the input through an actual PTY.

## Analysis and closure rationale

Script, -c, -m, symlink and actual PTY REPL checks confirm -P and PYTHONSAFEPATH suppress automatic unsafe paths; environment, -E and -I controls agree with CPython.

[PR #4611](https://github.com/RustPython/RustPython/pull/4611): connect -P, the environment and safe_path flags; [PR #5049](https://github.com/RustPython/RustPython/pull/5049): condition automatic path insertion on safe_path; [PR #8605](https://github.com/RustPython/RustPython/pull/8605): resolve script paths for path insertion.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The four -m -E/-I fixture lookup failures are expected: those options remove the explicit module search environment. TERM=dumb caused a basic REPL fallback in both interpreters.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`746cb0493f73`](https://github.com/RustPython/RustPython/commit/746cb0493f7371304ceafec88c56e5de59155b95), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-command-746cb0493f-01-1dbcf35b.stdout](../../evidence/history/logs/issue-4541-case-01/historical-command-746cb0493f-01-1dbcf35b.stdout).
- [Full reused historical-command-746cb0493f-01-1dbcf35b.stderr](../../evidence/history/logs/issue-4541-case-01/historical-command-746cb0493f-01-1dbcf35b.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

<details>
<summary>Execution records (52 runs)</summary>

- **[4541-cpython-command-Eenv1](../../evidence/additional11/agent-a/4541-cpython-command-Eenv1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-command-Eenv1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-command-Eenv1.stderr.txt).
- **[4541-cpython-command-I](../../evidence/additional11/agent-a/4541-cpython-command-I.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-command-I.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-command-I.stderr.txt).
- **[4541-cpython-command-P](../../evidence/additional11/agent-a/4541-cpython-command-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-command-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-command-P.stderr.txt).
- **[4541-cpython-command-default](../../evidence/additional11/agent-a/4541-cpython-command-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-command-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-command-default.stderr.txt).
- **[4541-cpython-command-env0](../../evidence/additional11/agent-a/4541-cpython-command-env0.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-command-env0.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-command-env0.stderr.txt).
- **[4541-cpython-command-env1](../../evidence/additional11/agent-a/4541-cpython-command-env1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-command-env1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-command-env1.stderr.txt).
- **[4541-cpython-command-envempty](../../evidence/additional11/agent-a/4541-cpython-command-envempty.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-command-envempty.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-command-envempty.stderr.txt).
- **[4541-cpython-module-Eenv1](../../evidence/additional11/agent-a/4541-cpython-module-Eenv1.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-module-Eenv1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-module-Eenv1.stderr.txt).
- **[4541-cpython-module-I](../../evidence/additional11/agent-a/4541-cpython-module-I.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-module-I.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-module-I.stderr.txt).
- **[4541-cpython-module-P](../../evidence/additional11/agent-a/4541-cpython-module-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-module-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-module-P.stderr.txt).
- **[4541-cpython-module-default](../../evidence/additional11/agent-a/4541-cpython-module-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-module-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-module-default.stderr.txt).
- **[4541-cpython-module-env0](../../evidence/additional11/agent-a/4541-cpython-module-env0.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-module-env0.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-module-env0.stderr.txt).
- **[4541-cpython-module-env1](../../evidence/additional11/agent-a/4541-cpython-module-env1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-module-env1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-module-env1.stderr.txt).
- **[4541-cpython-module-envempty](../../evidence/additional11/agent-a/4541-cpython-module-envempty.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-module-envempty.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-module-envempty.stderr.txt).
- **[4541-cpython-repl-P](../../evidence/additional11/agent-a/4541-cpython-repl-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-repl-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-repl-P.stderr.txt).
- **[4541-cpython-repl-default](../../evidence/additional11/agent-a/4541-cpython-repl-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-repl-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-repl-default.stderr.txt).
- **[4541-cpython-repl-env1](../../evidence/additional11/agent-a/4541-cpython-repl-env1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-repl-env1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-repl-env1.stderr.txt).
- **[4541-cpython-script-Eenv1](../../evidence/additional11/agent-a/4541-cpython-script-Eenv1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-script-Eenv1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-script-Eenv1.stderr.txt).
- **[4541-cpython-script-I](../../evidence/additional11/agent-a/4541-cpython-script-I.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-script-I.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-script-I.stderr.txt).
- **[4541-cpython-script-P](../../evidence/additional11/agent-a/4541-cpython-script-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-script-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-script-P.stderr.txt).
- **[4541-cpython-script-default](../../evidence/additional11/agent-a/4541-cpython-script-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-script-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-script-default.stderr.txt).
- **[4541-cpython-script-env0](../../evidence/additional11/agent-a/4541-cpython-script-env0.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-script-env0.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-script-env0.stderr.txt).
- **[4541-cpython-script-env1](../../evidence/additional11/agent-a/4541-cpython-script-env1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-script-env1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-script-env1.stderr.txt).
- **[4541-cpython-script-envempty](../../evidence/additional11/agent-a/4541-cpython-script-envempty.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-script-envempty.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-script-envempty.stderr.txt).
- **[4541-cpython-symlink-P](../../evidence/additional11/agent-a/4541-cpython-symlink-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-symlink-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-symlink-P.stderr.txt).
- **[4541-cpython-symlink-default](../../evidence/additional11/agent-a/4541-cpython-symlink-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-cpython-symlink-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-cpython-symlink-default.stderr.txt).
- **[4541-rustpython-command-Eenv1](../../evidence/additional11/agent-a/4541-rustpython-command-Eenv1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-command-Eenv1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-command-Eenv1.stderr.txt).
- **[4541-rustpython-command-I](../../evidence/additional11/agent-a/4541-rustpython-command-I.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-command-I.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-command-I.stderr.txt).
- **[4541-rustpython-command-P](../../evidence/additional11/agent-a/4541-rustpython-command-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-command-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-command-P.stderr.txt).
- **[4541-rustpython-command-default](../../evidence/additional11/agent-a/4541-rustpython-command-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-command-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-command-default.stderr.txt).
- **[4541-rustpython-command-env0](../../evidence/additional11/agent-a/4541-rustpython-command-env0.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-command-env0.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-command-env0.stderr.txt).
- **[4541-rustpython-command-env1](../../evidence/additional11/agent-a/4541-rustpython-command-env1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-command-env1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-command-env1.stderr.txt).
- **[4541-rustpython-command-envempty](../../evidence/additional11/agent-a/4541-rustpython-command-envempty.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-command-envempty.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-command-envempty.stderr.txt).
- **[4541-rustpython-module-Eenv1](../../evidence/additional11/agent-a/4541-rustpython-module-Eenv1.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-module-Eenv1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-module-Eenv1.stderr.txt).
- **[4541-rustpython-module-I](../../evidence/additional11/agent-a/4541-rustpython-module-I.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-module-I.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-module-I.stderr.txt).
- **[4541-rustpython-module-P](../../evidence/additional11/agent-a/4541-rustpython-module-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-module-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-module-P.stderr.txt).
- **[4541-rustpython-module-default](../../evidence/additional11/agent-a/4541-rustpython-module-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-module-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-module-default.stderr.txt).
- **[4541-rustpython-module-env0](../../evidence/additional11/agent-a/4541-rustpython-module-env0.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-module-env0.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-module-env0.stderr.txt).
- **[4541-rustpython-module-env1](../../evidence/additional11/agent-a/4541-rustpython-module-env1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-module-env1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-module-env1.stderr.txt).
- **[4541-rustpython-module-envempty](../../evidence/additional11/agent-a/4541-rustpython-module-envempty.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-module-envempty.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-module-envempty.stderr.txt).
- **[4541-rustpython-repl-P](../../evidence/additional11/agent-a/4541-rustpython-repl-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-repl-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-repl-P.stderr.txt).
- **[4541-rustpython-repl-default](../../evidence/additional11/agent-a/4541-rustpython-repl-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-repl-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-repl-default.stderr.txt).
- **[4541-rustpython-repl-env1](../../evidence/additional11/agent-a/4541-rustpython-repl-env1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-repl-env1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-repl-env1.stderr.txt).
- **[4541-rustpython-script-Eenv1](../../evidence/additional11/agent-a/4541-rustpython-script-Eenv1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-script-Eenv1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-script-Eenv1.stderr.txt).
- **[4541-rustpython-script-I](../../evidence/additional11/agent-a/4541-rustpython-script-I.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-script-I.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-script-I.stderr.txt).
- **[4541-rustpython-script-P](../../evidence/additional11/agent-a/4541-rustpython-script-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-script-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-script-P.stderr.txt).
- **[4541-rustpython-script-default](../../evidence/additional11/agent-a/4541-rustpython-script-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-script-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-script-default.stderr.txt).
- **[4541-rustpython-script-env0](../../evidence/additional11/agent-a/4541-rustpython-script-env0.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-script-env0.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-script-env0.stderr.txt).
- **[4541-rustpython-script-env1](../../evidence/additional11/agent-a/4541-rustpython-script-env1.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-script-env1.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-script-env1.stderr.txt).
- **[4541-rustpython-script-envempty](../../evidence/additional11/agent-a/4541-rustpython-script-envempty.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-script-envempty.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-script-envempty.stderr.txt).
- **[4541-rustpython-symlink-P](../../evidence/additional11/agent-a/4541-rustpython-symlink-P.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-symlink-P.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-symlink-P.stderr.txt).
- **[4541-rustpython-symlink-default](../../evidence/additional11/agent-a/4541-rustpython-symlink-default.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4541-rustpython-symlink-default.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4541-rustpython-symlink-default.stderr.txt).

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
