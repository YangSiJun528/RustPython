# Review 25 resolved issues for closure

## Summary

Please review these 25 issues for closure: their reported problems are resolved within the verified scope.

While looking for issues to work on, I spent time investigating reports whose problems were already resolved. Closing them would make outstanding work easier to find and avoid repeated investigation.

I selected cases with clear reproduction conditions and expected outcomes, then used OpenAI Codex extensively to investigate, run checks against `main` at [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c), and draft the reports. I reviewed the results and manually checked some cases.

Repeated checks and independent rechecks are documented in the [24-issue audit](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/independent/2026-10-06-closure24/README.md) and [#6697 audit](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/independent/2026-10-06-6697/README.md). I have not reviewed every underlying fix at the code level.

I consider this an appropriate use of AI because the selected cases have directly checkable outcomes. The closure recommendations are limited to what the recorded checks demonstrate.

## Details

### [#2527 — REPL expressions inside blocks](https://github.com/RustPython/RustPython/issues/2527)

In an actual interactive REPL, the original loop now displays `0` through `9`, and the file-write block displays `5`, matching CPython.

- Related changes: [PR #7067](https://github.com/RustPython/RustPython/pull/7067): display interactive expressions in nested blocks.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/2527/README.md).

### [#3418 — Native OrderedDict export](https://github.com/RustPython/RustPython/issues/3418)

`from _collections import OrderedDict` now succeeds. Ordering, `move_to_end`, `popitem`, reverse iteration and equality checks agree with CPython.

- Related changes: [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native OrderedDict and class-method descriptors.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/3418/README.md).

### [#3430 — ElementTree parsing valid XML](https://github.com/RustPython/RustPython/issues/3430)

`etree.XML("<root></root>")` now parses successfully without the reported `TypeError`. Valid XML samples with children, text, attributes, namespaces and UTF-8 also agree with CPython.

- Related changes: [PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept None as the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parsing.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/3430/README.md).

### [#3846 — Disassembly support used by modulefinder](https://github.com/RustPython/RustPython/issues/3846)

`dis.opmap`, `dis.EXTENDED_ARG` and `dis._unpack_opargs` now work with actual bytecode. `modulefinder` correctly analyzes the tested local import graph, and all 17 original `ModuleFinderTest` tests pass.

- Related changes: [PR #5377](https://github.com/RustPython/RustPython/pull/5377): provide dis exports and bytecode/import scanning.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/3846/README.md).

### [#4506 — SymPy import with the reported versions](https://github.com/RustPython/RustPython/issues/4506)

SymPy 1.11.1 with mpmath 1.2.1 now imports successfully. The previously failing `is_commutative` assignment in `power.py` executes, and the reported `Pow` path succeeds.

- Related changes: [PR #6390](https://github.com/RustPython/RustPython/pull/6390): install declared slot descriptors even over inherited attributes.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4506/README.md).

### [#4527 — Finalization of a global object](https://github.com/RustPython/RustPython/issues/4527)

The original global-object example now calls `__del__` and prints `deleted!` during normal interpreter shutdown, with exit code `0` and no stderr.

- Related changes: [PR #6934](https://github.com/RustPython/RustPython/pull/6934): module finalization during shutdown.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4527/README.md).

### [#4541 — Safe path flags and path insertion](https://github.com/RustPython/RustPython/issues/4541)

`-P` and `PYTHONSAFEPATH` now suppress automatic unsafe path insertion for scripts, `-c`, `-m` and the interactive REPL. Symlink, `-E` and `-I` checks also agree with CPython.

- Related changes: [PR #4611](https://github.com/RustPython/RustPython/pull/4611): connect -P, the environment and safe_path flags; [PR #5049](https://github.com/RustPython/RustPython/pull/5049): condition automatic path insertion on safe_path; [PR #8605](https://github.com/RustPython/RustPython/pull/8605): resolve script paths for path insertion.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4541/README.md).

### [#4690 — Native class-method descriptor type](https://github.com/RustPython/RustPython/issues/4690)

The raw `dict.__dict__["fromkeys"]` descriptor now has type `classmethod_descriptor`, while the bound `dict.fromkeys` has type `builtin_function_or_method`, matching CPython. Descriptor binding and the additional native descriptors checked agree with CPython.

- Related changes: [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native OrderedDict and class-method descriptors.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4690/README.md).

### [#4762 — Negative dynamic format width](https://github.com/RustPython/RustPython/issues/4762)

`'%*s' % (-5, 'abc')` now returns `'abc  '`, preserving the required two trailing spaces. Positive, zero and additional negative widths also agree with CPython.

- Related changes: [PR #4766](https://github.com/RustPython/RustPython/pull/4766): left alignment for negative dynamic widths.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4762/README.md).

### [#4769 — Deque subclass pickle state](https://github.com/RustPython/RustPython/issues/4769)

The original deque subclass regression test now passes. Pickle protocols 0–5 preserve subclass type, contents, `maxlen`, instance attributes and slots.

- Related changes: [PR #7699](https://github.com/RustPython/RustPython/pull/7699): include __getstate__ in deque reduction.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4769/README.md).

### [#4784 — README API documentation link](https://github.com/RustPython/RustPython/issues/4784)

The README documentation link now serves the RustPython API documentation, including crate and API entries. The retrieved page identifies RustPython 0.6.0.

- Documentation: [Published API documentation](https://docs.rs/rustpython/latest/rustpython/).
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4784/README.md).

### [#4786 — Surrogate in a type name](https://github.com/RustPython/RustPython/issues/4786)

The original surrogate in the type name is preserved, and creating the type raises `UnicodeEncodeError`, matching CPython. The uncaught exception correctly exits with code `1`.

- Related changes: [PR #5629](https://github.com/RustPython/RustPython/pull/5629): retain surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4786/README.md).

### [#4856 — Lambda in a class decorator](https://github.com/RustPython/RustPython/issues/4856)

The original class-decorator example now compiles without the reported Rust compiler panic. Running the supplied source still raises `NameError` for the undefined `BaseFTests` in both interpreters; valid `mock.patch` and nested-capture examples execute successfully.

- Related changes: [PR #8138](https://github.com/RustPython/RustPython/pull/8138): visit class decorators before entering their class scope.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4856/README.md).

### [#4907 — Await in an async comprehension](https://github.com/RustPython/RustPython/issues/4907)

The original async function now compiles. The example in the issue comment also runs through an actual asyncio event loop, completes both awaited sleeps and prints `lc done`.

- Related changes: [PR #5334](https://github.com/RustPython/RustPython/pull/5334): compile await inside an async comprehension.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4907/README.md).

### [#4908 — AST round trip for a starred subscript](https://github.com/RustPython/RustPython/issues/4908)

The original starred subscript now unparses to valid Python syntax and reparses successfully. Additional slice and starred-subscript combinations preserve the AST structure.

- Related changes: [PR #5121](https://github.com/RustPython/RustPython/pull/5121): valid subscript-tuple unparsing.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4908/README.md).

### [#4937 — Email Subject with an unknown encoding](https://github.com/RustPython/RustPython/issues/4937)

The original email `Subject` with the unknown `X` encoding is now returned without `KeyError`. Additional unknown-encoding and malformed-header cases were also checked.

- Related changes: [PR #5663](https://github.com/RustPython/RustPython/pull/5663): unknown encoded-word recovery.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4937/README.md).

### [#4950 — Bool numeric format codes](https://github.com/RustPython/RustPython/issues/4950)

`False` and `True` now format like CPython for the originally reported format codes, the comment’s `n` and `d` codes, and the tested width and precision combinations.

- Related changes: [PR #5012](https://github.com/RustPython/RustPython/pull/5012): update the parser/format dependency · [Parser PR #91](https://github.com/RustPython/Parser/pull/91).
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4950/README.md).

### [#4970 — Locale formatting with LC_ALL unset](https://github.com/RustPython/RustPython/issues/4970)

With `LC_ALL` unset and `LANG` and `LC_NUMERIC` set to `en_US.UTF-8`, the original `test_locale` and the integer/float locale tests pass without skips or expected failures.

- Related changes: [PR #7350](https://github.com/RustPython/RustPython/pull/7350): use locale grouping, separator and decimal-point data.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4970/README.md).

### [#5179 — Builtin buffer methods](https://github.com/RustPython/RustPython/issues/5179)

The builtin and subclass types tested now expose the expected buffer methods. Writable access, release and resizing after release agree with CPython; resizing while a buffer is exported is correctly blocked.

- Related changes: [PR #8523](https://github.com/RustPython/RustPython/pull/8523): PEP 688 methods and managed buffer exports.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/5179/README.md).

### [#5656 — Invalid escape warning in a bytes literal](https://github.com/RustPython/RustPython/issues/5656)

Compiling the original bytes literal now emits the required `SyntaxWarning` for the invalid escape while preserving the bytes value. Treating the warning as an error also works.

- Related changes: [PR #7164](https://github.com/RustPython/RustPython/pull/7164): warn about invalid string and bytes escapes.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/5656/README.md).

### [#5699 — Blockers for colored tracebacks](https://github.com/RustPython/RustPython/issues/5699)

All four reported blockers now work: class patterns, `frame.f_builtins`, `sys.stdlib_module_names` and `except*`. Actual uncaught exceptions produce colored tracebacks, including builtin and missing-stdlib suggestions, matching CPython in the tested cases.

- Related changes: [PR #6110](https://github.com/RustPython/RustPython/pull/6110): class-pattern code generation; [PR #6568](https://github.com/RustPython/RustPython/pull/6568): provide both frame.f_builtins and sys.stdlib_module_names; [PR #6530](https://github.com/RustPython/RustPython/pull/6530): except* code generation and exception-group handling.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/5699/README.md).

### [#6429 — Py_GIL_DISABLED configuration value](https://github.com/RustPython/RustPython/issues/6429)

`sysconfig.get_config_var("Py_GIL_DISABLED")` now returns the defined value `1` in the verified POSIX RustPython build.

- Related changes: [PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose the build-time Py_GIL_DISABLED value.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/6429/README.md).

### [#6697 — Symbol-table error while importing pytest](https://github.com/RustPython/RustPython/issues/6697)

The original function with a generator expression inside `finally` now compiles and runs without the reported symbol-table error. The real pytest 9.1.1 `pytester.py` module compiles and imports, its affected `pytest_runtest_protocol` body passes a controlled execution check, and a small run through `pytest.console_main` reports `2 passed`. This verifies the reported compiler/import blocker; it does not establish that the full xonsh test suite passes.

- Related changes: [PR #8507](https://github.com/RustPython/RustPython/pull/8507): preserve symbol-table cursors when compiling an extra copy of a `finally` block.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/6697/README.md).

### [#8052 — Ellipsis type name](https://github.com/RustPython/RustPython/issues/8052)

The type name is now `ellipsis`, and its representation is `<class 'ellipsis'>`, matching CPython. The type alias and existing JSON regression tests also pass.

- Related changes: [PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/8052/README.md).

### [#8494 — Classmethod and staticmethod annotations](https://github.com/RustPython/RustPython/issues/8494)

`classmethod` and `staticmethod` now cache `__annotations__` and `__annotate__` on the wrapper. Assignment and deletion leave the wrapped function unchanged. The module-level example from the issue, a separate function-local variant and the original regression test pass.

- Related changes: [PR #8701](https://github.com/RustPython/RustPython/pull/8701): cache and assign annotation attributes on the wrapper.
- [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/8494/README.md).

AI assistance: verification and drafting with OpenAI Codex.
