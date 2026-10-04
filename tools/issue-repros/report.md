# Review 16 resolved RustPython issues for closure

I rechecked the reports below on [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c) on October 4, 2026. The original failures reproduce on the historical revisions recorded in each case; the current results satisfy the reported behavior. The documentation link was checked separately through docs.rs.

Could you review these results and close the corresponding issues? Each entry links to its executable input, local run command and recorded evidence.

- **[#2527 — expressions in blocks don't print their value in the REPL](https://github.com/RustPython/RustPython/issues/2527)**
  - Previously: Neither block displayed its expression values.
  - Verified result and reason to close: Interactive compilation now emits expression output inside module-level blocks. The original loop displays 0–9 and the `with` block displays 5, resolving both missing-output examples on Linux with `TERM=xterm`.
  - Related change: [PR #7067](https://github.com/RustPython/RustPython/pull/7067): interactive expression handling in nested blocks.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/2527/README.md)

- **[#3418 — Introduce `_collections.OrderedDict` type (a.k.a. `collections.OrderedDict`)](https://github.com/RustPython/RustPython/issues/3418)**
  - Previously: ImportError importing OrderedDict from _collections.
  - Verified result and reason to close: A native `OrderedDict` is now exported from `_collections`. The requested `from _collections import OrderedDict` import succeeds, satisfying the reported missing-export issue.
  - Related change: [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native `OrderedDict` implementation and export.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/3418/README.md)

- **[#3430 — etree.XML raises TypeError on valid XML](https://github.com/RustPython/RustPython/issues/3430)**
  - Previously: TypeError: Expected type 'str', not 'NoneType'.
  - Verified result and reason to close: The parser accepts the explicit `None` encoding argument passed by ElementTree. The original `etree.XML("<root></root>")` call now returns the expected empty root element, resolving the reported `TypeError`.
  - Related change: [PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept `None` for the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parser implementation.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/3430/README.md)

- **[#4527 — top level objects are not deleted before script finalized](https://github.com/RustPython/RustPython/issues/4527)**
  - Previously: No finalizer output at process shutdown.
  - Verified result and reason to close: Shutdown now clears `__main__` globals while the facilities needed by finalizers remain available. The original global object's `__del__` prints `deleted!` during shutdown, satisfying the reported finalization behavior.
  - Related change: [PR #6934](https://github.com/RustPython/RustPython/pull/6934): module finalization during interpreter shutdown.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4527/README.md)

- **[#4690 — classmethod_descriptor](https://github.com/RustPython/RustPython/issues/4690)**
  - Previously: Raw dict.fromkeys descriptor has type classmethod.
  - Verified result and reason to close: Native class methods now use the dedicated `classmethod_descriptor` type. `dict.__dict__["fromkeys"]` has that type, matching CPython and resolving the reported descriptor-type mismatch.
  - Related change: [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native class-method descriptor construction.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4690/README.md)

- **[#4762 — cformat star asterisk should behave differently when given negative sign](https://github.com/RustPython/RustPython/issues/4762)**
  - Previously: The negative-width assertion raises AssertionError.
  - Verified result and reason to close: Negative dynamic widths now select left alignment. The original `'%*s' % (-5, 'abc') == 'abc  '` assertion passes, including the two trailing spaces.
  - Related change: [PR #4766](https://github.com/RustPython/RustPython/pull/4766): preserve left alignment for negative dynamic widths.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4762/README.md)

- **[#4784 — docs.rs page linked in the readme doesn't exist " rustpython-0.1.2 is not a library."](https://github.com/RustPython/RustPython/issues/4784)**
  - Previously: The reported docs destination did not provide the expected API documentation.
  - Verified result and reason to close: The README's docs.rs destination now serves published RustPython 0.6.0 API documentation. The linked API documentation is available, satisfying the original documentation-link report.
  - Related change: [Published API documentation](https://docs.rs/rustpython/latest/rustpython/).
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4784/README.md)

- **[#4786 — Type name cannot contain surrogates](https://github.com/RustPython/RustPython/issues/4786)**
  - Previously: Creates a type whose name contains a replacement character.
  - Verified result and reason to close: String literals preserve lone surrogates, and type-name validation rejects them. The original `type("A\udcdcB", (), {})` input now raises the expected `UnicodeEncodeError`, resolving the silent replacement-character behavior.
  - Related change: [PR #5629](https://github.com/RustPython/RustPython/pull/5629): preserve surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4786/README.md)

- **[#4856 — Assertion failed: table.sub_tables.is_empty() when decorator class takes a lambda argument.](https://github.com/RustPython/RustPython/issues/4856)**
  - Previously: Compiler panic: table.sub_tables.is_empty().
  - Verified result and reason to close: Class decorators are scanned before entering the class scope, matching code-generation order and keeping nested symbol tables aligned. The original source now compiles without the reported `table.sub_tables.is_empty()` panic.
  - Related change: [PR #8138](https://github.com/RustPython/RustPython/pull/8138): correct class-decorator scope scanning order.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4856/README.md)

- **[#4908 — ast.parse() fails to handle "A[1:2, *l]" after it is parsed and unparsed.](https://github.com/RustPython/RustPython/issues/4908)**
  - Previously: Unparses to A[(1:2, *l)]; reparsing raises SyntaxError.
  - Verified result and reason to close: The unparser handles nonempty subscript tuples containing starred elements without introducing invalid parentheses around slices. `A[1:2, *l]` now unparses and reparses successfully, resolving the reported invalid-syntax output.
  - Related change: [PR #5121](https://github.com/RustPython/RustPython/pull/5121): correct subscript-tuple unparsing.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4908/README.md)

- **[#4937 — email.message_from_string.get() fails parses the special text](https://github.com/RustPython/RustPython/issues/4937)**
  - Previously: Subject retrieval raises KeyError: x.
  - Verified result and reason to close: Unknown encoded-word encodings are handled by the email parser's invalid-input recovery. Retrieving the original X-encoded Subject now completes without the reported `KeyError: x`.
  - Related change: [PR #5663](https://github.com/RustPython/RustPython/pull/5663): email update that handles unknown encoded-word encodings.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4937/README.md)

- **[#5181 — `format()` does not support locales for 'n' presentation type](https://github.com/RustPython/RustPython/issues/5181)**
  - Previously: With en_US.UTF-8: result '123456789', matches False.
  - Verified result and reason to close: The `n` formatter uses locale grouping and separator settings. With `en_US.UTF-8`, `format(123456789, 'n')` now returns `'123,456,789'`, satisfying the reported grouping requirement.
  - Related change: [PR #7350](https://github.com/RustPython/RustPython/pull/7350): locale-aware numeric formatting.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/5181/README.md)

- **[#5656 — Not properly checking for invalid escape seqeunce \X](https://github.com/RustPython/RustPython/issues/5656)**
  - Previously: The assertion passes without the required invalid-escape warning.
  - Verified result and reason to close: Compilation detects invalid escapes in bytes literals and emits the corresponding warning. The original bytes assertion still passes and now emits the missing `SyntaxWarning` for `\X`, satisfying the report.
  - Related change: [PR #7164](https://github.com/RustPython/RustPython/pull/7164): invalid string and bytes escape warnings.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/5656/README.md)

- **[#6429 — `sysconfig.get_config_var('Py_GIL_DISABLED')` returns `None`](https://github.com/RustPython/RustPython/issues/6429)**
  - Previously: Py_GIL_DISABLED is None.
  - Verified result and reason to close: Build-time configuration now defines `Py_GIL_DISABLED` as `1`. On POSIX/macOS, `sysconfig.get_config_var("Py_GIL_DISABLED")` returns `1`, resolving the reported missing configuration value.
  - Related change: [PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose `Py_GIL_DISABLED` in build-time variables.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/6429/README.md)

- **[#6790 — Support xz](https://github.com/RustPython/RustPython/issues/6790)**
  - Previously: The decorated function raises SkipTest: requires lzma.
  - Verified result and reason to close: The unconditional `lzma = None` override was removed from `requires_lzma`. With the module available, `requires_lzma()(dummy)` now invokes the function successfully; the requested removal of the forced skip is complete.
  - Related change: [PR #7896](https://github.com/RustPython/RustPython/pull/7896): remove the unconditional lzma skip override.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/6790/README.md)

- **[#8052 — `type(...).__name__` is `'EllipsisType'` instead of `'ellipsis'`](https://github.com/RustPython/RustPython/issues/8052)**
  - Previously: EllipsisType and <class 'EllipsisType'>.
  - Verified result and reason to close: The built-in type is now named `ellipsis`. The original query returns `ellipsis` and `<class 'ellipsis'>`, matching CPython and resolving both reported naming outputs.
  - Related change: [PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.
  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/8052/README.md)

Runtime checks used macOS ARM64 except the REPL check, which used Linux ARM64. Related PRs identify matching source changes; exact first-fixing commits were not established by parent/commit execution comparisons.

AI assistance: OpenAI Codex assisted with verification, evidence analysis, executable packaging and drafting.
