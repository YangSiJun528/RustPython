# Review 16 resolved issues for closure

I rechecked the 16 reports below and found that their reported failures or missing behaviors are resolved. Could you review these results and close the corresponding issues?

Verification used [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c) on October 4, 2026: macOS ARM64 for the script comparisons, Linux ARM64 for the interactive REPL, and a separate HTTP check for the documentation link. Each linked report contains direct reproduction commands, historical/current results and supporting evidence.

The related PRs contain source changes matching these results; the exact first fixing commit was not established.

- **[#2527](https://github.com/RustPython/RustPython/issues/2527) — REPL expressions inside blocks.**
  The original loop and `with` block previously displayed no expression values. They now display `0`–`9` and `5`, respectively, in the Linux REPL with `TERM=xterm`.
  [PR #7067](https://github.com/RustPython/RustPython/pull/7067): interactive expression handling in nested blocks. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/2527/README.md).

- **[#3418](https://github.com/RustPython/RustPython/issues/3418) — Native `OrderedDict` export.**
  `from _collections import OrderedDict` previously raised `ImportError`. The native implementation is now exported and the import succeeds.
  [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native `OrderedDict` implementation and export. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/3418/README.md).

- **[#3430](https://github.com/RustPython/RustPython/issues/3430) — ElementTree parsing valid XML.**
  `etree.XML("<root></root>")` previously raised a `TypeError` for a `None` encoding. It now returns an empty `root` element; the parser accepts that encoding argument.
  [PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept `None` for the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parser implementation. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/3430/README.md).

- **[#4527](https://github.com/RustPython/RustPython/issues/4527) — Finalization of a global object.**
  The original object's `__del__` previously produced no output at shutdown. It now prints `deleted!` when the interpreter clears the module globals.
  [PR #6934](https://github.com/RustPython/RustPython/pull/6934): module finalization during interpreter shutdown. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4527/README.md).

- **[#4690](https://github.com/RustPython/RustPython/issues/4690) — Native class-method descriptor type.**
  `type(dict.__dict__["fromkeys"]).__name__` now returns `classmethod_descriptor` instead of `classmethod`, matching CPython. Native class methods use the dedicated descriptor type.
  [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native class-method descriptor construction. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4690/README.md).

- **[#4762](https://github.com/RustPython/RustPython/issues/4762) — Negative dynamic format width.**
  The original `'%*s' % (-5, 'abc') == 'abc  '` assertion now passes. Negative width selects left alignment, including the required two trailing spaces.
  [PR #4766](https://github.com/RustPython/RustPython/pull/4766): preserve left alignment for negative dynamic widths. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4762/README.md).

- **[#4784](https://github.com/RustPython/RustPython/issues/4784) — README API documentation link.**
  The linked docs.rs page previously reported that `rustpython-0.1.2` was not a library. The README destination now serves the published RustPython 0.6.0 API documentation.
  [Published API documentation](https://docs.rs/rustpython/latest/rustpython/). [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4784/README.md).

- **[#4786](https://github.com/RustPython/RustPython/issues/4786) — Surrogate in a type name.**
  `type("A\udcdcB", (), {})` previously created a class with a replacement character. It now raises the expected `UnicodeEncodeError`: the literal preserves the surrogate and type-name validation rejects it.
  [PR #5629](https://github.com/RustPython/RustPython/pull/5629): preserve surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4786/README.md).

- **[#4856](https://github.com/RustPython/RustPython/issues/4856) — Compiler panic with a lambda in a class decorator.**
  Compiling the original decorated-class source now succeeds without the `table.sub_tables.is_empty()` panic. Decorator scope scanning now matches code-generation order.
  [PR #8138](https://github.com/RustPython/RustPython/pull/8138): correct class-decorator scope scanning order. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4856/README.md).

- **[#4908](https://github.com/RustPython/RustPython/issues/4908) — AST round trip for a starred subscript.**
  Unparsing `A[1:2, *l]` previously produced invalid `A[(1:2, *l)]`. It now preserves valid subscript syntax and reparses successfully.
  [PR #5121](https://github.com/RustPython/RustPython/pull/5121): correct subscript-tuple unparsing. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4908/README.md).

- **[#4937](https://github.com/RustPython/RustPython/issues/4937) — Email Subject with an unknown encoding.**
  Retrieving the original X-encoded Subject now completes without `KeyError: x`. The email parser handles the unknown encoded-word encoding through its invalid-input recovery.
  [PR #5663](https://github.com/RustPython/RustPython/pull/5663): email update that handles unknown encoded-word encodings. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4937/README.md).

- **[#5181](https://github.com/RustPython/RustPython/issues/5181) — Locale-aware `n` formatting.**
  With `en_US.UTF-8` selected, `format(123456789, 'n')` now returns `'123,456,789'` instead of `'123456789'`, using the locale's grouping and separator.
  [PR #7350](https://github.com/RustPython/RustPython/pull/7350): locale-aware numeric formatting. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/5181/README.md).

- **[#5656](https://github.com/RustPython/RustPython/issues/5656) — Invalid escape warning in a bytes literal.**
  The original bytes assertion still passes, but compilation now emits the previously missing `SyntaxWarning` for `\X`. Both the bytes value and the warning were checked.
  [PR #7164](https://github.com/RustPython/RustPython/pull/7164): invalid string and bytes escape warnings. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/5656/README.md).

- **[#6429](https://github.com/RustPython/RustPython/issues/6429) — `Py_GIL_DISABLED` configuration value.**
  `sysconfig.get_config_var('Py_GIL_DISABLED')` now returns `1` instead of `None` on the tested POSIX/macOS build. The value is defined in the build-time configuration.
  [PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose `Py_GIL_DISABLED` in build-time variables. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/6429/README.md).

- **[#6790](https://github.com/RustPython/RustPython/issues/6790) — Forced lzma test skip.**
  The unconditional `lzma = None` override has been removed. With lzma available, `requires_lzma()(dummy)` now invokes the function instead of raising `SkipTest`, satisfying the requested removal of the forced skip.
  [PR #7896](https://github.com/RustPython/RustPython/pull/7896): remove the unconditional lzma skip override. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/6790/README.md).

- **[#8052](https://github.com/RustPython/RustPython/issues/8052) — Ellipsis type name.**
  `type(...).__name__` and the type's repr now give `ellipsis` and `<class 'ellipsis'>`, matching CPython, in place of the previous `EllipsisType` spelling.
  [PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name. [Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/8052/README.md).

AI assistance: verification and drafting with OpenAI Codex.
