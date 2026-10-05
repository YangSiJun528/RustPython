# Review 24 independently verified issues for closure

I independently rechecked the reports below and found sufficient evidence that their reported problems are resolved. Could you review these results and close the corresponding issues?

Verification used [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c) on October 5, 2026. The fresh runs used macOS ARM64 and, for the explicitly identified slot B cases, x86_64 RustPython through Rosetta. CPython comparisons used 3.14.6 ARM64. The documentation-link case was checked against the actual served API content.

The related changes explain the observed behavior; the exact first fixing commits were not established. Historical failure logs were reused, while the current results were independently executed. Each detailed report separates those evidence sources and states its limits.

This is an unsubmitted issue-body draft. #4613, #5181 and #6790 remain partially resolved and are excluded from this closure request; see the [remaining issues](recheck/not-ready.md). #6697 is outside these independent audits and is not counted.

- **[#2527](https://github.com/RustPython/RustPython/issues/2527) — REPL expressions inside blocks.**
  Actual PTY sessions now display 0–9 from the original loop and 5 from the file-write block. The same CPython input agrees; displayhook and function-scope controls also pass.
  [PR #7067](https://github.com/RustPython/RustPython/pull/7067): display interactive expressions in nested blocks.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/2527/README.md).

- **[#3418](https://github.com/RustPython/RustPython/issues/3418) — Native OrderedDict export.**
  The native import succeeds, and ordering, move_to_end, popitem, reversed, equality and a subclass sample agree with CPython.
  [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native OrderedDict and class-method descriptors.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/3418/README.md).

- **[#3430](https://github.com/RustPython/RustPython/issues/3430) — ElementTree parsing valid XML.**
  The original empty root parses successfully. Valid child, text, attribute, namespace and UTF-8 samples agree with CPython.
  [PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept None as the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parsing.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/3430/README.md).

- **[#3846](https://github.com/RustPython/RustPython/issues/3846) — Disassembly support used by modulefinder.**
  The three requested dis APIs operate on actual bytecode. A five-module import graph and all 17 original ModuleFinderTest tests pass without skip or expectedFailure.
  [PR #5377](https://github.com/RustPython/RustPython/pull/5377): provide dis exports and bytecode/import scanning.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/3846/README.md).

- **[#4506](https://github.com/RustPython/RustPython/issues/4506) — SymPy import with the reported versions.**
  SymPy 1.11.1 with mpmath 1.2.1 imports successfully. Tracing observes the original power.py:378 is_commutative assignment, and the reported Pow path succeeds.
  [PR #6390](https://github.com/RustPython/RustPython/pull/6390): install declared slot descriptors even over inherited attributes.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4506/README.md).

- **[#4527](https://github.com/RustPython/RustPython/issues/4527) — Finalization of a global object.**
  The unchanged original lifetime pattern prints deleted! at interpreter shutdown, with exit 0 and no stderr. An explicit-del control was checked separately.
  [PR #6934](https://github.com/RustPython/RustPython/pull/6934): module finalization during shutdown.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4527/README.md).

- **[#4541](https://github.com/RustPython/RustPython/issues/4541) — Safe path flags and path insertion.**
  Script, -c, -m, symlink and actual PTY REPL checks confirm -P and PYTHONSAFEPATH suppress automatic unsafe paths; environment, -E and -I controls agree with CPython.
  [PR #4611](https://github.com/RustPython/RustPython/pull/4611): connect -P, the environment and safe_path flags; [PR #5049](https://github.com/RustPython/RustPython/pull/5049): condition automatic path insertion on safe_path; [PR #8605](https://github.com/RustPython/RustPython/pull/8605): resolve script paths for path insertion.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4541/README.md).

- **[#4690](https://github.com/RustPython/RustPython/issues/4690) — Native class-method descriptor type.**
  Both original descriptor queries return classmethod_descriptor. Binding and representative additional native descriptors agree with CPython.
  [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native OrderedDict and class-method descriptors.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4690/README.md).

- **[#4762](https://github.com/RustPython/RustPython/issues/4762) — Negative dynamic format width.**
  The original assertion preserves the two trailing spaces in `'abc  '`. Positive, zero and additional negative-width controls also agree with CPython.
  [PR #4766](https://github.com/RustPython/RustPython/pull/4766): left alignment for negative dynamic widths.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4762/README.md).

- **[#4769](https://github.com/RustPython/RustPython/issues/4769) — Deque subclass pickle state.**
  The original regression test passes. Protocols 0–5 preserve dict/slots state, type, contents and maxlen in 36 subclass round trips.
  [PR #7699](https://github.com/RustPython/RustPython/pull/7699): include __getstate__ in deque reduction.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4769/README.md).

- **[#4784](https://github.com/RustPython/RustPython/issues/4784) — README API documentation link.**
  The README destination returned HTTP 200 and an actual RustPython 0.6.0 API page, including crate and API content; status alone was not the oracle.
  [Published API documentation](https://docs.rs/rustpython/latest/rustpython/).

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4784/README.md).

- **[#4786](https://github.com/RustPython/RustPython/issues/4786) — Surrogate in a type name.**
  The original surrogate is retained and type creation raises UnicodeEncodeError, matching CPython. Exit 1 for the uncaught exception is expected.
  [PR #5629](https://github.com/RustPython/RustPython/pull/5629): retain surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4786/README.md).

- **[#4856](https://github.com/RustPython/RustPython/issues/4856) — Lambda in a class decorator.**
  The original source compiles without the Rust compiler panic. Executing that original source raises BaseFTests NameError in both interpreters. Separate valid mock.patch and nested-capture controls execute and restore the patched function.
  [PR #8138](https://github.com/RustPython/RustPython/pull/8138): visit class decorators before entering their class scope.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4856/README.md).

- **[#4907](https://github.com/RustPython/RustPython/issues/4907) — Await in an async comprehension.**
  The original async function compiles. The comment's actual asyncio event-loop and two awaited sleeps finish with lc done.
  [PR #5334](https://github.com/RustPython/RustPython/pull/5334): compile await inside an async comprehension.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4907/README.md).

- **[#4908](https://github.com/RustPython/RustPython/issues/4908) — AST round trip for a starred subscript.**
  The original starred subscript unparses to valid syntax and reparses; extended combinations preserve AST structure.
  [PR #5121](https://github.com/RustPython/RustPython/pull/5121): valid subscript-tuple unparsing.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4908/README.md).

- **[#4937](https://github.com/RustPython/RustPython/issues/4937) — Email Subject with an unknown encoding.**
  The original X-encoded Subject is returned without KeyError. Unknown encodings and related malformed-header controls were also checked.
  [PR #5663](https://github.com/RustPython/RustPython/pull/5663): unknown encoded-word recovery.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4937/README.md).

- **[#4950](https://github.com/RustPython/RustPython/issues/4950) — Bool numeric format codes.**
  False and True match CPython for the original codes, the comment's n/d codes and width/precision controls: 34 recorded results.
  [PR #5012](https://github.com/RustPython/RustPython/pull/5012): update the parser/format dependency · [Parser PR #91](https://github.com/RustPython/Parser/pull/91).

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4950/README.md).

- **[#4970](https://github.com/RustPython/RustPython/issues/4970) — Locale formatting with LC_ALL unset.**
  With LC_ALL absent and LANG/LC_NUMERIC=en_US.UTF-8, the unmodified original test_locale and two int/float locale tests pass, with no skip or expectedFailure.
  [PR #7350](https://github.com/RustPython/RustPython/pull/7350): use locale grouping, separator and decimal-point data.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/4970/README.md).

- **[#5179](https://github.com/RustPython/RustPython/issues/5179) — Builtin buffer methods.**
  Seven builtin/subclass types expose the expected buffer behavior. Writable flags, release, blocked resize during export and successful resize after release agree with CPython.
  [PR #8523](https://github.com/RustPython/RustPython/pull/8523): PEP 688 methods and managed buffer exports.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/5179/README.md).

- **[#5656](https://github.com/RustPython/RustPython/issues/5656) — Invalid escape warning in a bytes literal.**
  The bytes value is preserved and compilation emits the required SyntaxWarning for the invalid escape. Warning presence and warning-as-error behavior were checked.
  [PR #7164](https://github.com/RustPython/RustPython/pull/7164): warn about invalid string and bytes escapes.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/5656/README.md).

- **[#5699](https://github.com/RustPython/RustPython/issues/5699) — Blockers for colored tracebacks.**
  All four listed blockers execute successfully. Colored traceback APIs and four actual uncaught exception paths match CPython, including builtin and missing-stdlib suggestions.
  [PR #6110](https://github.com/RustPython/RustPython/pull/6110): class-pattern code generation; [PR #6568](https://github.com/RustPython/RustPython/pull/6568): provide both frame.f_builtins and sys.stdlib_module_names; [PR #6530](https://github.com/RustPython/RustPython/pull/6530): except* code generation and exception-group handling.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/5699/README.md).

- **[#6429](https://github.com/RustPython/RustPython/issues/6429) — Py_GIL_DISABLED configuration value.**
  sysconfig.get_config_var("Py_GIL_DISABLED") is defined as 1 in the verified POSIX RustPython build.
  [PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose the build-time Py_GIL_DISABLED value.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/6429/README.md).

- **[#8052](https://github.com/RustPython/RustPython/issues/8052) — Ellipsis type name.**
  The name and repr are `ellipsis` and `<class 'ellipsis'>`; the types alias, JSON error note and existing JSON regression tests also pass.
  [PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/8052/README.md).

- **[#8494](https://github.com/RustPython/RustPython/issues/8494) — Classmethod and staticmethod annotations.**
  Both wrappers support the two annotation attributes, cache values in the wrapper, and isolate writes/deletes from the wrapped function. The original unresolved-name input and regression test pass.
  [PR #8701](https://github.com/RustPython/RustPython/pull/8701): cache and assign annotation attributes on the wrapper.

  - [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/recheck/cases/8494/README.md).

AI assistance: verification, evidence packaging and drafting with OpenAI Codex.
