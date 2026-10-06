# Comprehensions in finally blocks prevent pytest import (#6697)

[Original issue](https://github.com/RustPython/RustPython/issues/6697). **Resolved in the reported scope; closure recommended.** Independent runs at the baseline below accept the exact reduced input, preserve finally-block behavior across comprehension types and exit paths, compile and import the affected pytest module, and execute its actual `pytest_runtest_protocol` finally body. A small run through `pytest.console_main` passes two tests on both interpreters.

Verified on commit: [`f39b054b9c8cbbf884f53123eef028131789990c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c), October 6, 2026. This does not establish a first fixing commit or claim the full xonsh suite works.

## Original scope and independent plan

The [fresh issue snapshot](evidence/issue.json) was retrieved at **2026-10-06T02:34:52Z**. Its state was `open`, `updated_at` was `2026-09-03T00:43:44Z`, and `closed_at` was null. All six [comments](evidence/comments.json) were read before the [source-first plan](SOURCE-FIRST-PLAN.md) was saved. Previous local reports were consulted only afterwards for evidence locations and method details. Their conclusions were not used as test results.

The original launch sequence was:

```sh
rustpython -V
# Python 3.13.0alpha (heads/master:6ff7b3ed2

git clone https://github.com/xonsh/xonsh
cd xonsh/
rust-pytest
```

The failure occurs before xonsh test execution: the entrypoint imports `pytest.console_main`, pytest imports `_pytest.legacypath`, and that imports `_pytest.pytester.HookRecorder`. Compiling `_pytest/pytester.py` raises a `SyntaxError` at this line inside `pytest_runtest_protocol`:

```python
new_fds = {t[0] for t in lines2} - {t[0] for t in lines1}
```

The recorded error is `no symbol table available in pytest_runtest_protocol (type: Function)`. The March 27 comment supplies a smaller generator-expression example, reproduced exactly below. The May 24 clarification says that defining the function must succeed silently and calling it must return `None`; executing the function was not necessary to trigger the historical error. The September claim that #8507 fixed the issue was treated as a hypothesis to check.

The report does not specify the original pytest version, xonsh revision, dependency versions, CPU architecture, macOS release, or complete entrypoint/environment. Its `<reported-home>/` paths indicate a macOS-style installation. No original dependency configuration was invented, and no repository was cloned.

## Environment and executable provenance

Both fresh interpreters ran sequentially in slot A with cwd `<workspace>`, on macOS **26.5.2**, build **25F84**, Darwin **25.5.0**, ARM64. Both executables are Mach-O ARM64 and report 64-bit pointers. This is native ARM64 verification, not an x86_64/Rosetta run.

RustPython executable and realpath:

```text
<survey>/.build/slot-a/verification/rustpython
```

SHA256: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.

Fresh `-B -S -VV` output, exit 0, empty stderr:

```text
Python 3.14.0.alpha (heads/main:f39b054b9, Oct  4 2026, 13:53:35)
[RustPython 0.6.1 with rustc 1.99.0 (b940084d7 2026-09-28)]
```

Baseline linkage is supported by the newly computed binary hash matching the retained `optimized_sqlite` [build record](evidence/reused/build-variants-a.json), which records the full baseline SHA and successful build with default features plus `sqlite`, profile `verification` inheriting `release`, and Rust 1.99.0. The retained [build stderr](evidence/reused/sqlite-verification-build.stderr) records successful completion. The retained [Cargo build output](evidence/reused/rustpython-vm-build-output.txt) contains the matching embedded commit/version. The fresh runtime banner agrees. These are reused build records, not a new build or an independent attestation of every historical build input; checkout HEAD alone is not the provenance argument.

CPython launch path:

```text
<home>/.local/bin/python3
```

Resolved executable:

```text
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14
```

SHA256: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

Fresh `-B -S -VV` output, exit 0, empty stderr:

```text
Python 3.14.6 (main, Jun 23 2026, 15:46:31) [Clang 22.1.3 ]
```

The [RustPython identity record](records/rp-identity-v2.json) verifies actual imports of `os`, `json`, `struct`, and `importlib.metadata` from the repository's `Lib`. Their hashes, the compiler source, the executed snippet, and its `testutils.py` dependency match `git show f39b054:<path>` exactly in [source-comparison.json](evidence/source-comparison.json). CPython imports its own standard library, confirmed in its [identity record](records/cp-identity-v2.json).

Both interpreters use this same existing package directory:

```text
<survey>/verification-tools/package-site
```

The actual imported versions are pytest **9.1.1**, pluggy **1.6.0**, packaging **26.3**, iniconfig **2.3.0**, and Pygments **2.21.0**. The identity records include actual module paths and SHA256 values. The installed `_pytest/pytester.py` has SHA256 `9e791d0a3446b04324e70bb939712f8d490005ad13eb46ab3249592baa08ff17` and still contains the original set-comprehension expression inside the same method. A [verbatim source copy](evidence/reused/pytester.py.txt) is preserved; it was not changed or substituted for the executed installation.

## Copyable setup and commands

Choose absolute paths and assign these shell variables before running the commands:

- `SRC`: existing RustPython source at the verified commit, including its matching `Lib`.
- `RP`: the existing RustPython executable for that commit.
- `CP`: an existing CPython 3.14.6 executable.
- `SITE`: the existing package directory containing pytest 9.1.1 and the versions listed above.
- `CASE`: a new writable reproduction directory; save the shown inputs under `CASE/inputs`.
- `TIMEOUT`: an existing GNU `timeout` executable. This audit used `/opt/homebrew/bin/timeout`.

The commands use `en_US.UTF-8`, available on the audited system. The exact original paths remain in the Environment section and raw records; no package install or build is part of these reproduction commands.

```sh
export SRC CASE RP CP SITE TIMEOUT
mkdir -p "$CASE/inputs" "$CASE/tmp"
cd "$SRC"

run_rp() {
    env -i PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin \
        HOME="$HOME" LC_ALL=en_US.UTF-8 \
        PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
        PYTEST_ADDOPTS= PYTEST_PLUGINS= TMPDIR="$CASE/tmp" \
        SITE="$SITE" CASE="$CASE" SRC="$SRC" \
        RUSTPYTHONPATH="$SRC/Lib:$SITE" \
        "$TIMEOUT" --signal=TERM --kill-after=5s 45s \
        "$RP" -B -S "$@"
}
run_cp() {
    env -i PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin \
        HOME="$HOME" LC_ALL=en_US.UTF-8 \
        PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
        PYTEST_ADDOPTS= PYTEST_PLUGINS= TMPDIR="$CASE/tmp" \
        SITE="$SITE" CASE="$CASE" SRC="$SRC" PYTHONPATH="$SITE" \
        "$TIMEOUT" --signal=TERM --kill-after=5s 45s \
        "$CP" -B -S "$@"
}
```

`env -i` excludes ambient Python startup/path/warning settings. `-S` excludes site initialization while explicit paths expose the installed packages. `-B` and `PYTHONDONTWRITEBYTECODE=1` disable bytecode writes. Pytest plugin autoloading and its cache provider are disabled. Generated outputs are directed into this new audit directory. Existing source, tests, dependencies, reports, and build products were not modified.

The recording wrapper [run-v2.pl](run-v2.pl) uses the same environment and a 45-second timeout, with forced termination five seconds later if needed. Each invocation has its own JSON record with argv, cwd, complete replacement environment, timestamps, elapsed time, timeout/status, executable hash, input hashes, and exact stdout/stderr. Native output files are preserved alongside those records.

Python code blocks are formatted for readability. Their syntax trees match the executed inputs; the archived `.py.txt` files retain the exact executed source.

## Exact reduced reproducer

`inputs/original.py`, copied directly from the issue comment:

```python
def a():
    try:
        return
    finally:
        (0 for a in ())
```

SHA256: `cc057db4113ba172a9ece7d32c64c29e3a04b2d088ad0a958680008c8510b95e`, also matching the retained historical input.

`inputs/call-original.py` is a separate runtime control:

```python
from original import a

assert a() is None
print("returned None")
```

Run sequentially:

```sh
run_rp "$CASE/inputs/original.py"
run_cp "$CASE/inputs/original.py"
run_rp "$CASE/inputs/call-original.py"
run_cp "$CASE/inputs/call-original.py"
```

Expected and observed on both interpreters: the original definition exits **0** with empty stdout and stderr. The call control exits **0**, stdout is `returned None` followed by a newline, and stderr is empty. No timeout. Records: [RustPython definition](records/rp-original.json), [CPython definition](records/cp-original.json), [RustPython call](records/rp-call.json), [CPython call](records/cp-call.json).

## Comprehension and control-flow checks

`inputs/controls.py` compiles each expression in a finally block, separately testing return, normal completion, and propagated exception. It captures a local variable, checks that finally executes once, and places another nested scope after the early-exit branches:

```python
expressions = {
    "generator": "list(value + x for x in (1, 2))",
    "list": "[value + x for x in (1, 2)]",
    "set": "sorted({value + x for x in (1, 2)})",
    "dict": "list({x: value + x for x in (1, 2)}.values())",
}
for kind, expression in expressions.items():
    source = """
def exercise(mode, value, log):
    try:
        if mode == 'return':
            return value
        if mode == 'exception':
            raise ValueError('original exception')
        (lambda: 'scope after early exit')()
    finally:
        log.append(EXPRESSION)
""".replace("EXPRESSION", expression)
    namespace = {}
    exec(compile(source, "<finally-" + kind + ">", "exec"), namespace)
    for mode in ("return", "normal", "exception"):
        log = []
        try:
            result = namespace["exercise"](mode, 10, log)
        except ValueError as error:
            assert mode == "exception"
            assert str(error) == "original exception"
            result = "ValueError"
        else:
            assert result == (10 if mode == "return" else None)
            assert mode != "exception"
        assert log == [[11, 12]], (kind, mode, log)
        print(kind, mode, result, log)
print("12 finally/comprehension cases passed")
```

```sh
run_rp "$CASE/inputs/controls.py"
run_cp "$CASE/inputs/controls.py"
```

Expected and observed on both interpreters: exit **0**, no timeout, empty stderr, and identical stdout:

```text
generator return 10 [[11, 12]]
generator normal None [[11, 12]]
generator exception ValueError [[11, 12]]
list return 10 [[11, 12]]
list normal None [[11, 12]]
list exception ValueError [[11, 12]]
set return 10 [[11, 12]]
set normal None [[11, 12]]
set exception ValueError [[11, 12]]
dict return 10 [[11, 12]]
dict normal None [[11, 12]]
dict exception ValueError [[11, 12]]
12 finally/comprehension cases passed
```

Records: [RustPython controls](records/rp-controls.json), [CPython controls](records/cp-controls.json).

The existing, unmodified `extra_tests/snippets/syntax_try.py` also ran on both interpreters. Its regression cases cover early return, break/continue, one-time finally execution, a generator's `return (yield ...)`, nested functions/classes/lambdas, and nested scopes after early exits. The current snippet is broader than the original #8507 addition.

```sh
run_rp "$SRC/extra_tests/snippets/syntax_try.py"
run_cp "$SRC/extra_tests/snippets/syntax_try.py"
```

Expected: all snippet assertions succeed. Observed: exit **0**, no timeout, empty stderr, identical stdout below, including its initial blank line:

```text

<class 'BaseException'>
boom
kablam
boom <class 'AssertionError'>
kablam
kablam
kablam
boom <class 'AssertionError'>
boom <class 'NameError'>
boom <class 'TypeError'>
```

Records: [RustPython snippet](records/rp-syntax-try.json), [CPython snippet](records/cp-syntax-try.json). Verbatim copies of the [snippet](evidence/reused/syntax_try.py.txt) and [testutils](evidence/reused/testutils.py.txt) accompany the report. The runs used the original tracked files, not these copies.

## Original pytest import route and affected method

`inputs/pytest-probe.py` explicitly compiles the complete installed source, imports the same entrypoint and class from the reported traceback, then executes the actual pytest method with controlled file-list inputs. The controlled method check replaces only the new in-memory checker's file-list provider; no installed file is edited and no `lsof` subprocess is run.

```python
import os

path = os.path.join(os.environ["SITE"], "_pytest", "pytester.py")
with open(path, encoding="utf-8") as file:
    source = file.read()
assert "new_fds = {t[0] for t in lines2} - {t[0] for t in lines1}" in source
compile(source, path, "exec")
print("complete pytester.py compile passed")

from pytest import console_main
from _pytest.pytester import HookRecorder, LsofFdLeakChecker
import pytest
import _pytest.pytester

assert callable(console_main)
assert HookRecorder.__module__ == "_pytest.pytester"
print("pytest", pytest.__version__)
print("console_main and HookRecorder imports passed")
print("pytester path", _pytest.pytester.__file__)

checker = LsofFdLeakChecker()
files = iter([[("1", "/before")], [("1", "/before"), ("2", "/new")]])
checker.get_open_files = lambda: next(files)


class Item:
    location = ("controlled.py", 1, "test_control")

    def __init__(self):
        self.warnings = []

    def warn(self, warning):
        self.warnings.append(warning)


item = Item()
protocol = checker.pytest_runtest_protocol(item)
assert next(protocol) is None
try:
    protocol.send("completed")
except StopIteration as stop:
    assert stop.value == "completed"
else:
    raise AssertionError("generator did not stop")
assert len(item.warnings) == 1
assert "1 FD leakage detected" in str(item.warnings[0])
assert "('2', '/new')" in str(item.warnings[0])
print("actual pytest_runtest_protocol finally body passed: one expected leak warning")
```

```sh
run_rp "$CASE/inputs/pytest-probe.py"
run_cp "$CASE/inputs/pytest-probe.py"
```

Expected: no compiler error, successful imports, `completed` preserved as the generator's return value, and exactly one warning for the newly introduced file descriptor. Observed on both interpreters: exit **0**, no timeout, empty stderr, identical stdout:

```text
complete pytester.py compile passed
pytest 9.1.1
console_main and HookRecorder imports passed
pytester path <survey>/verification-tools/package-site/_pytest/pytester.py
actual pytest_runtest_protocol finally body passed: one expected leak warning
```

Records: [RustPython pytest probe](records/rp-pytest-probe.json), [CPython pytest probe](records/cp-pytest-probe.json). The warning is captured by the test's `Item.warn`, so it does not appear on stderr.

## Small pytest execution

`inputs/test_6697.py`:

```python
from original import a


def test_original_function():
    assert a() is None


def test_finally_comprehension_on_return():
    seen = []

    def run():
        try:
            return "value"
        finally:
            seen.append(
                {t[0] for t in [("new", 1), ("old", 2)]} - {t[0] for t in [("old", 2)]}
            )

    assert run() == "value"
    assert seen == [{"new"}]
```

`inputs/run-pytest.py` retains the reported entrypoint import and calls it:

```python
from pytest import console_main

raise SystemExit(console_main())
```

`inputs/pytest.ini`:

```ini
[pytest]
```

```sh
run_rp "$CASE/inputs/run-pytest.py" -q -p no:cacheprovider \
    -c "$CASE/inputs/pytest.ini" --rootdir "$CASE/inputs" \
    --confcutdir "$CASE/inputs" --basetemp "$CASE/tmp/pytest-rp" \
    "$CASE/inputs/test_6697.py"
run_cp "$CASE/inputs/run-pytest.py" -q -p no:cacheprovider \
    -c "$CASE/inputs/pytest.ini" --rootdir "$CASE/inputs" \
    --confcutdir "$CASE/inputs" --basetemp "$CASE/tmp/pytest-cp" \
    "$CASE/inputs/test_6697.py"
```

Expected: both tests pass through the original import route. RustPython stdout, exit **0**, no timeout:

```text
..                                                                       [100%]
2 passed in 0.01s
```

CPython stdout, exit **0**, no timeout:

```text
..                                                                       [100%]
2 passed in 0.00s
```

Both produce the same stderr deprecation warning. It was preserved rather than suppressed:

```text
<6697-audit>/inputs/run-pytest.py:3: PytestRemovedIn10Warning: pytest.console_main() is deprecated and will be removed in pytest 10.
It was never intended for programmatic use; use pytest.main() instead.
See https://docs.pytest.org/en/stable/deprecations.html#console-main
  raise SystemExit(console_main())
```

Records: [RustPython pytest smoke](records/rp-pytest-smoke.json), [CPython pytest smoke](records/cp-pytest-smoke.json). This warning is shared pytest behavior and does not reproduce the reported SyntaxError.

## Historical evidence and source explanation

The historical check was **not rerun**. The preserved [historical execution record](evidence/reused/historical-3909b18eac-01.json) identifies commit [`3909b18eac642d824cd5c1157f452e8765269a2e`](https://github.com/RustPython/RustPython/commit/3909b18eac642d824cd5c1157f452e8765269a2e), exit **1**, no timeout, and the same reduced-input SHA256 used by this audit. Its associated [build provenance](evidence/reused/historical-build-provenance.json) records Rust 1.96.1, ARM64, and binary SHA256 `87dd696f95e674408d0801ddc788d086483fb24a65c818e61f4f8f222a2ad311`. This is a historical comparison revision, not the reporter's exact `6ff7b3ed2` executable.

Historical stdout is empty. Native [historical stderr](evidence/reused/historical-3909b18eac-01.stderr) includes six destructor warnings followed by:

```text
  File "<survey>/repros/6697/issue-6697-case-02/source-01.py", line 5
    (0 for a in ())
    ^
SyntaxError: no symbol table available in a (type: Function)
```

The native log is retained in full. This historical failure supports that the exact reduced input exercised the reported compiler failure; it is not a fresh result from this audit.

[PR #8507](https://github.com/RustPython/RustPython/pull/8507), source commit [`2a793fcdd1461001a0078cc89d34833205f4f30b`](https://github.com/RustPython/RustPython/commit/2a793fcdd1461001a0078cc89d34833205f4f30b), adds saving/restoring of the symbol-table cursors around an extra copy of a finally body emitted on early exit. Otherwise compiling that copy consumes nested-scope entries needed when the finally body is compiled again. The [retained patch](evidence/change-8507.patch) also adds regression cases to `syntax_try.py`. `git merge-base --is-ancestor` confirms this commit is included in the tested baseline, exit 0.

The baseline additionally seeks to the finally body's own nested-scope positions before compiling that copy. [Current source](evidence/current-compiler-finally.txt) and [blame](evidence/current-compiler-blame.txt) show that follow-up in commit `f87cfe7e7a`; its [patch](evidence/followup-change.patch) is included. The tested baseline therefore includes more than the original #8507 change. The extra scope-order checks and current snippet validate the resulting behavior here. No parent/fix commit pair was built or executed, so the first fixing boundary remains unestablished.

## Preservation, evidence quality, and limits

[Preservation comparison](evidence/preservation-comparison.json) confirms **147 selected pre-existing files unchanged** between before/after hashes, including both executables, affected package trees and existing cache files, relevant tracked sources, reused historical/build records, the prior report, and the style reference. All seven selected tracked files match the baseline; `git diff --exit-code` is empty. This is a targeted preservation inventory, not a claim that every file on the machine was hashed.

All interpreter invocations were sequential, used `-B` and `PYTHONDONTWRITEBYTECODE=1`, and had bounded timeouts. No build, clone, worktree, environment creation, package install, source/test/dependency edit, commit, push, issue/PR/comment submission, or issue-state change occurred. The user-requested no-build constraint means workspace Cargo tests/clippy were not run; this audit reused executables and ran the relevant behavior checks directly.

Four initial version/identity records used a Perl recorder with an empty-file list-context defect: it emitted a warning while serializing empty stderr. Those raw logs and original records remain preserved, and the interpreter processes themselves exited 0. The corrected `run-v2.pl` records empty stderr explicitly as a string; all four identity/version commands were repeated under distinct `*-v2` names before behavioral testing. Conclusions use those corrected records and the unchanged native outputs. This recording defect did not alter test input, interpreter state, or expected outcomes.

The exact original pytest/xonsh environment cannot be reconstructed from the issue. The installed pytest version here is explicitly 9.1.1, and the xonsh test suite and original `rust-pytest` script were not run. Native `lsof` integration was not tested; the actual affected method was driven with controlled inputs. These limits do not leave the specific import-time symbol-table failure untested: the exact minimal reproducer, complete affected module compilation, original imports, real finally body, and small entrypoint run all succeeded.

**Closure recommendation:** close #6697 for the reported compiler/import error, citing the verified baseline and pytest version, while retaining the limits above. The report does not establish general xonsh or pytest compatibility.

[Machine-readable assessment](assessment.json), [source-first plan](SOURCE-FIRST-PLAN.md), [source hash comparison](evidence/source-comparison.json), and [execution records](records/) support this conclusion. AI assistance: OpenAI Codex.
