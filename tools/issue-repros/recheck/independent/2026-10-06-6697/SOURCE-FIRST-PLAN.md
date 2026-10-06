# Independent source-first plan: RustPython #6697

Saved 2026-10-06 after fresh GitHub issue body/comments retrieval, before consulting any previous local verification report or judgment. Scope comes from https://github.com/RustPython/RustPython/issues/6697 and its six comments. The issue API was first successfully read at approximately 2026-10-06T02:34Z; it reports state `open`, updated_at `2026-09-03T00:43:44Z`, and no closed_at value. The browser result was stale (two-month crawl) and is not relied on for current state. The issue's own September closure claim is evidence to test, not an accepted conclusion.

## Original input and execution path

The issue reports `rustpython -V` as `Python 3.13.0alpha (heads/master:6ff7b3ed2`, then `git clone https://github.com/xonsh/xonsh`, `cd xonsh/`, `rust-pytest`. The macOS-style traceback paths are `<reported-home>/.local/bin/rust-pytest` and `<reported-home>/.local/lib/rustpython3.13t/site-packages/`. Exact OS release, CPU, xonsh revision, pytest version, dependency versions, entrypoint script, and complete environment are absent. Do not manufacture them or claim to reproduce that environment exactly.

The failure occurs while importing pytest: `pytest.__init__` imports `_pytest.legacypath`, which imports `_pytest.pytester.HookRecorder`; compiling `_pytest/pytester.py` fails at the expression below in `pytest_runtest_protocol`:

```python
new_fds = {t[0] for t in lines2} - {t[0] for t in lines1}
```

Reported result: `SyntaxError: no symbol table available in pytest_runtest_protocol (type: Function)`. This is a compilation/import blocker, before xonsh tests execute.

Comment 4143594774 provides this complete smaller reproducer:

```python
def a():
    try:
        return
    finally:
        (0 for a in ())
```

Comment 4529407891 says CPython merely defines the function without output; calling it returns None. It explicitly confirms the failure needs only loading the file, not calling the function. The issue thus includes finally/comprehension symbol-table handling, not only the isolated set subtraction expression. Comment 5518397585 claims #8507 fixed it; inspect that source later without inferring an untested first-fix boundary. Comment 5518567210 asks for confirmation on latest main.

## Minimum closure scope and independent checks

1. Save and run the exact minimal function-definition input on the supplied baseline and installed CPython. Expected exit 0 and empty stdout/stderr. Separately call it, expecting None.
2. Exercise each comprehension kind (generator, list, set, dictionary) in finally blocks, on return and exception paths, plus branch/re-entry controls and captured locals. Check CPython parity and actual values, not only absence of the historical message.
3. Identify installed pytest version/path and compile its real `_pytest/pytester.py`, checking that the originally reported function/expression remains present. Exercise `from pytest import console_main` and import `_pytest.pytester`, with other plugins disabled if a CLI control is used. Attempt a minimal pytest execution through the same import route, with all writable outputs redirected into this audit. Capture unrelated blockers distinctly.
4. A closure recommendation requires success for the exact minimal reproducer and meaningful finally/comprehension controls, plus evidence that the original pytest compile/import blocker is removed. An unrelated later pytest blocker limits end-to-end pytest compatibility; report it explicitly. Absence of exact original xonsh/pytest versions limits exact historical replay. Do not equate these bounded checks with the entire xonsh suite working.
5. Verify executable provenance and actual imported Lib, not just checkout HEAD. Obtain absolute binary path, SHA256, -V/sys.version, architecture, and available build records tying binary to f39b054b9c8cbbf884f53123eef028131789990c. Identify actual CPython path/version/architecture and relevant package files. If linkage cannot be established, qualify the baseline claim.
6. Inspect the relevant current compiler source and #8507 history after this plan. A source change can explain a fix but is not an executed before/after boundary.

## Constraints and recording

Own slot A only: source/cwd `<workspace>`; candidate executable `cleanup-issues/2026-10-04T155029+0900/.build/slot-a/verification/rustpython`. All interpreter invocations, including CPython and identity probes, must run sequentially. Reuse installed files. No build, clone, worktree, target, environment, dependency, source, or existing-test modifications. No remote mutation. No further agents. Use `-B`, `PYTHONDONTWRITEBYTECODE=1`, bounded subprocess timeouts, and record argv/cwd/environment/time/status/stdout/stderr/input SHA256. New files are restricted to this audit directory. Preserve and compare hashes for relevant existing binaries, package source, tracked source, prior reports, and evidence read. Clearly label reused records as historical. Final report will be English, detailed, with copyable commands and actual outputs, no tables or collapsed sections.
