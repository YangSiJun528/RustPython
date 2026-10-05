# Verification environment and evidence mapping

These reports describe completed October 5, 2026 executions at
`f39b054b9c8cbbf884f53123eef028131789990c`. Publishing this packet did not rerun
the interpreters or build a new executable.

## Executables and actual standard library

| Slot | Existing source/cwd | Existing executable | SHA-256 |
|---|---|---|---|
| A | `<workspace>` | `<survey>/.build/slot-a/verification/rustpython` | `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99` |
| B | `<slot-b-source>` | `<survey>/.build/slot-b/saved/current-f39-x86/rustpython` | `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871` |
| CPython | The same cwd as its paired run | `<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14` | `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef` |

The host is macOS 26.5.2 ARM64. Slot A is native ARM64; B is x86_64 through
Rosetta. Both RustPython binaries report `heads/main:f39b054b9`, Python
3.14.0.alpha and RustPython 0.6.1. CPython is 3.14.6 ARM64. The B command alias
`<home>/.local/bin/python3` resolves to the CPython path above.

Both source HEADs are the baseline. Its source tree is
`c50acd5f61ac5f4257b25baa832155888a9c7667` and Lib tree is
`2f62efb194a326f4abef6d2a61b0c5babc09e96b`. B can import main's `Lib` before
its `RUSTPYTHONPATH` setting. Actual module paths were inspected, and all 2,324
tracked Lib files in both locations matched the baseline blobs.

- [A runtime and source identity](evidence/additional11/agent-a/fresh-provenance.json).
- [B file, package and binary identity](evidence/additional11/agent-b/fresh-file-provenance.json).
- [B actual runtime](evidence/additional11/agent-b/provenance-rustpython.stdout.txt).
- [CPython actual runtime](evidence/additional11/agent-b/provenance-cpython.stdout.txt).
- [Earlier B identity and import checks](evidence/initial16/agent-b/source-lib-identification.json).

## Reading and replaying archived commands

Machine-specific roots are replaced consistently. This is a publication edit,
not a change to the completed local evidence. The [export manifest](export-manifest.json)
records both original and exported SHA-256 values.

| Placeholder | Meaning |
|---|---|
| `<workspace>` | Existing main RustPython checkout |
| `<slot-b-source>` | Existing second source checkout, `issue-history-b/RustPython` |
| `<report-worktree>` | Existing `resolved-issue-reproducers/RustPython` checkout |
| `<survey>` | Existing `cleanup-issues/2026-10-04T155029+0900` directory under main |
| `<initial16-audit>` | Completed first independent audit; exported under `evidence/initial16/` |
| `<additional11-audit>` | Completed second independent audit; exported under `evidence/additional11/` |
| `<home>` | The original user's home directory |

An execution JSON preserves argv, cwd, environment overrides, exit code and
timeout, plus inline output or companion log references. These are recorded
commands with explicit placeholders. To replay, use already available verified
interpreters, map those roots to your setup, and copy the linked `.py.txt` input
back to its original `.py` name in a new scratch location. Keep companion input
files together and substitute the same roots inside the input where present.
Do not run an archived host orchestration script without reviewing its paths.

For an ordinary standalone input after that mapping:

```sh
RUSTPYTHONPATH="$RUSTPYTHON_SOURCE/Lib" PYTHONDONTWRITEBYTECODE=1 \
  "$RUSTPYTHON" -B "$REPRO_INPUT"
PYTHONDONTWRITEBYTECODE=1 "$CPYTHON" -B "$REPRO_INPUT"
```

Preserve the selected record's additional arguments and environment. The shared
additional-11 `probes.py` requires its issue number argument. SymPy uses the
reported 1.11.1 and mpmath 1.2.1 files; package installation was not replayed.
Locale tests require the named available locale, not a C-locale substitute.
The existing repository `test` sources are unmodified. The additional locale
comparison points only CPython's `test` namespace to those sources, keeping
CPython's own stdlib implementations.

REPL cases require an actual PTY. Their stdout and stderr are merged in the
terminal transcript; they exit with `os._exit(0)` after flushing to avoid saving
user history. In six additional-11 PTY records, the field named `started_utc`
was captured after `proc.wait()`, not before spawning. Raw metadata is retained;
this known timing-label error does not change the input, output or exit status.

## Resource limits and interpretation

Each slot belonged to one agent; synchronous process calls completed before the
next job in that slot. At most two behavior processes could run, one per slot.
No new clone, worktree, target, package environment or rebuild was created.
`-B` and `PYTHONDONTWRITEBYTECODE=1` prevented bytecode-cache writes. Existing
source, binaries, logs and caches were preserved.

Timeouts, wrong environments and startup failures are not resolution evidence.
An uncaught expected exception can legitimately exit 1 (#4786 and #5699), while
an exit-0 script that prints a missing feature is not a pass. #5656 also requires
the warning. #6429 does not require CPython and RustPython build values to match.

Historical evidence was reused and can involve different platforms, toolchains
or expanded inputs. It is never labeled a fresh execution. The related PRs
explain observed changes but have not been isolated by running each PR and its
parent. No exact first-fixing commit is claimed.
