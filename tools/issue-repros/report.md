# Review 16 resolved RustPython issues for closure

I rechecked the reports below on [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c) on October 4, 2026. The recorded historical failures and current outcomes are listed with their reproduction commands. The documentation link was checked separately through docs.rs.

Could you review these results and close the corresponding issues?

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

- **[#2527 — expressions in blocks don't print their value in the REPL](https://github.com/RustPython/RustPython/issues/2527)**

  On Linux, start the interactive interpreter in a scratch directory with a writable history directory:

  ```sh
  (
    rustpython_repro_bin="$PWD/target/release/rustpython"
    rustpython_repro_lib="$PWD/Lib"
    rustpython_repro_tmp=$(mktemp -d)
    mkdir -p "$rustpython_repro_tmp/config/rustpython"
    cd "$rustpython_repro_tmp" || exit
    TERM=xterm XDG_CONFIG_HOME="$rustpython_repro_tmp/config" \
      RUSTPYTHONPATH="$rustpython_repro_lib" "$rustpython_repro_bin"
  )
  ```

  Enter the two blocks below, pressing Enter on an empty line after each block. Use the REPL: running this as a script does not exercise expression display.

  ```python
  for i in range(10):
      i

  with open("repl-output.txt", "w") as f:
      f.write("hello")
  ```

  The current interpreter should display 0 through 9 after the loop and 5 after the `with` block, returning to the primary prompt after each. Enter `exit()` when finished.

  - **Before — [163cd1953377](https://github.com/RustPython/RustPython/commit/163cd1953377f4049e06fdae55c715889857a301) (nearest pre-issue main revision; approximate baseline):** Neither block displayed its expression values.
  - **After:** The loop displays 0 through 9; the with block displays 5.
  - **Analysis and closure rationale:** Interactive compilation now emits expression output inside module-level blocks. The original loop displays 0–9 and the `with` block displays 5, resolving both missing-output examples on Linux with `TERM=xterm`.
  - **Related change:** [PR #7067](https://github.com/RustPython/RustPython/pull/7067): interactive expression handling in nested blocks.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/2527/README.md)

- **[#3418 — Introduce `_collections.OrderedDict` type (a.k.a. `collections.OrderedDict`)](https://github.com/RustPython/RustPython/issues/3418)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'from _collections import OrderedDict'
  ```

  - **Before — [40fd9c2683d7](https://github.com/RustPython/RustPython/commit/40fd9c2683d76adf2b9ed0d77c055e2d2514c27d) (nearest pre-issue main revision; approximate baseline):** ImportError importing OrderedDict from _collections.
  - **After:** The import succeeds (exit 0).
  - **Analysis and closure rationale:** A native `OrderedDict` is now exported from `_collections`. The requested `from _collections import OrderedDict` import succeeds, satisfying the reported missing-export issue.
  - **Related change:** [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native `OrderedDict` implementation and export.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/3418/README.md)

- **[#3430 — etree.XML raises TypeError on valid XML](https://github.com/RustPython/RustPython/issues/3430)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
  import xml.etree.ElementTree as etree

  result = etree.XML("<root></root>")
  print(type(result).__name__, result.tag, result.text, len(result))
  '
  ```

  - **Before — [310578c422c9](https://github.com/RustPython/RustPython/commit/310578c422c9b3d76eb8c739136b972d78e37180) (nearest pre-issue main revision; approximate baseline):** TypeError: Expected type 'str', not 'NoneType'.
  - **After:** Element root None 0 (exit 0).
  - **Analysis and closure rationale:** The parser accepts the explicit `None` encoding argument passed by ElementTree. The original `etree.XML("<root></root>")` call now returns the expected empty root element, resolving the reported `TypeError`.
  - **Related change:** [PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept `None` for the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parser implementation.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/3430/README.md)

- **[#4527 — top level objects are not deleted before script finalized](https://github.com/RustPython/RustPython/issues/4527)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
  class X:
      def __del__(self):
          print("deleted!")


  x = X()
  '
  ```

  - **Before — [e5735cde67b8](https://github.com/RustPython/RustPython/commit/e5735cde67b86699bd68c8959167ecf2649a6f2d) (nearest pre-issue main revision; approximate baseline):** No finalizer output at process shutdown.
  - **After:** deleted! is printed at shutdown (exit 0).
  - **Analysis and closure rationale:** Shutdown now clears `__main__` globals while the facilities needed by finalizers remain available. The original global object's `__del__` prints `deleted!` during shutdown, satisfying the reported finalization behavior.
  - **Related change:** [PR #6934](https://github.com/RustPython/RustPython/pull/6934): module finalization during interpreter shutdown.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4527/README.md)

- **[#4690 — classmethod_descriptor](https://github.com/RustPython/RustPython/issues/4690)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'print(type(dict.__dict__["fromkeys"]).__name__)'
  ```

  - **Before — [8ff947e83a65](https://github.com/RustPython/RustPython/commit/8ff947e83a65b74c920edc63aed8a0a5854b8612) (nearest pre-issue main revision; approximate baseline):** Raw dict.fromkeys descriptor has type classmethod.
  - **After:** Raw descriptor has type classmethod_descriptor.
  - **Analysis and closure rationale:** Native class methods now use the dedicated `classmethod_descriptor` type. `dict.__dict__["fromkeys"]` has that type, matching CPython and resolving the reported descriptor-type mismatch.
  - **Related change:** [PR #8780](https://github.com/RustPython/RustPython/pull/8780): native class-method descriptor construction.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4690/README.md)

- **[#4762 — cformat star asterisk should behave differently when given negative sign](https://github.com/RustPython/RustPython/issues/4762)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'assert "%*s" % (-5, "abc") == "abc  "'
  ```

  - **Before — [c36e3612e7dd](https://github.com/RustPython/RustPython/commit/c36e3612e7dd1c7abd9fc7b76b912372bd26afbf) (nearest pre-issue main revision; approximate baseline):** The negative-width assertion raises AssertionError.
  - **After:** The assertion passes; two trailing spaces are retained.
  - **Analysis and closure rationale:** Negative dynamic widths now select left alignment. The original `'%*s' % (-5, 'abc') == 'abc  '` assertion passes, including the two trailing spaces.
  - **Related change:** [PR #4766](https://github.com/RustPython/RustPython/pull/4766): preserve left alignment for negative dynamic widths.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4762/README.md)

- **[#4784 — docs.rs page linked in the readme doesn't exist " rustpython-0.1.2 is not a library."](https://github.com/RustPython/RustPython/issues/4784)**

  ```sh
  curl --fail --location https://docs.rs/rustpython
  ```

  Follow redirects and inspect the returned API documentation. The recorded response was the RustPython 0.6.0 API page.

  - **Before — Original documentation-link report:** The reported docs destination did not provide the expected API documentation.
  - **After:** The README destination serves RustPython 0.6.0 API documentation.
  - **Analysis and closure rationale:** The README's docs.rs destination now serves published RustPython 0.6.0 API documentation. The linked API documentation is available, satisfying the original documentation-link report.
  - **Related change:** [Published API documentation](https://docs.rs/rustpython/latest/rustpython/).
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4784/README.md)

- **[#4786 — Type name cannot contain surrogates](https://github.com/RustPython/RustPython/issues/4786)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'print(repr(type("A\udcdcB", (), {})))'
  ```

  - **Before — [010640ccc8f7](https://github.com/RustPython/RustPython/commit/010640ccc8f74f56075df09a654352ae3d162d25) (nearest pre-issue main revision; approximate baseline):** Creates a type whose name contains a replacement character.
  - **After:** UnicodeEncodeError rejects the surrogate in the name (expected exit 1).
  - **Analysis and closure rationale:** String literals preserve lone surrogates, and type-name validation rejects them. The original `type("A\udcdcB", (), {})` input now raises the expected `UnicodeEncodeError`, resolving the silent replacement-character behavior.
  - **Related change:** [PR #5629](https://github.com/RustPython/RustPython/pull/5629): preserve surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4786/README.md)

- **[#4856 — Assertion failed: table.sub_tables.is_empty() when decorator class takes a lambda argument.](https://github.com/RustPython/RustPython/issues/4856)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
  source = """\
  import unittest
  from unittest import mock

  class MockedA(BaseFTests):
      pass

  @mock.patch("", lambda: 3)
  class MockedB(MockedA):
      def _asserts(self, val):
          pass
  """
  compile(source, "repro.py", "exec")
  print("compile_success")
  '
  ```

  This compiles the original source without executing it, directly testing the reported compiler panic.

  - **Before — [c7faae9b22ce](https://github.com/RustPython/RustPython/commit/c7faae9b22ce31a3ba1f2cc1cd3ad759b54ce100) (reported v0.2.0 release tag):** Compiler panic: table.sub_tables.is_empty().
  - **After:** compile_success (exit 0).
  - **Analysis and closure rationale:** Class decorators are scanned before entering the class scope, matching code-generation order and keeping nested symbol tables aligned. The original source now compiles without the reported `table.sub_tables.is_empty()` panic.
  - **Related change:** [PR #8138](https://github.com/RustPython/RustPython/pull/8138): correct class-decorator scope scanning order.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4856/README.md)

- **[#4908 — ast.parse() fails to handle "A[1:2, *l]" after it is parsed and unparsed.](https://github.com/RustPython/RustPython/issues/4908)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
  import ast

  code_1 = "A[1:2, *l]"
  tree_1 = ast.parse(code_1)  # work normally

  code_2 = ast.unparse(tree_1)
  print(code_2)  # str "A[1:2, *l]"
  tree_2 = ast.parse(code_2)  # fail
  '
  ```

  - **Before — [471ec268737c](https://github.com/RustPython/RustPython/commit/471ec268737c789ba861a6f7762128fc2ed21323) (revision identified in the report):** Unparses to A[(1:2, *l)]; reparsing raises SyntaxError.
  - **After:** A[1:2, *l] unparses and reparses successfully.
  - **Analysis and closure rationale:** The unparser handles nonempty subscript tuples containing starred elements without introducing invalid parentheses around slices. `A[1:2, *l]` now unparses and reparses successfully, resolving the reported invalid-syntax output.
  - **Related change:** [PR #5121](https://github.com/RustPython/RustPython/pull/5121): correct subscript-tuple unparsing.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4908/README.md)

- **[#4937 — email.message_from_string.get() fails parses the special text](https://github.com/RustPython/RustPython/issues/4937)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
  import email
  import email.policy

  mytext = "Subject:=?us-ascii?X?value?="
  em = email.message_from_string(mytext, policy=email.policy.default)
  em.get("Subject")
  '
  ```

  - **Before — [02840593bc56](https://github.com/RustPython/RustPython/commit/02840593bc56ae416ba2646166628f1712d6cf43) (revision identified in the report):** Subject retrieval raises KeyError: x.
  - **After:** The same retrieval completes (exit 0).
  - **Analysis and closure rationale:** Unknown encoded-word encodings are handled by the email parser's invalid-input recovery. Retrieving the original X-encoded Subject now completes without the reported `KeyError: x`.
  - **Related change:** [PR #5663](https://github.com/RustPython/RustPython/pull/5663): email update that handles unknown encoded-word encodings.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/4937/README.md)

- **[#5181 — `format()` does not support locales for 'n' presentation type](https://github.com/RustPython/RustPython/issues/5181)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
  import locale

  print("locale", locale.setlocale(locale.LC_ALL, "en_US.UTF-8"))
  print("result", repr(format(123456789, "n")))
  print("matches", format(123456789, "n") == "123,456,789")
  '
  ```

  The system must provide `en_US.UTF-8` (`locale -a`). The command selects that locale explicitly.

  - **Before — [a8ab7dd38814](https://github.com/RustPython/RustPython/commit/a8ab7dd3881437ad2eef31b3470427db20656a84) (nearest pre-issue main revision; approximate baseline):** With en_US.UTF-8: result '123456789', matches False.
  - **After:** With en_US.UTF-8: result '123,456,789', matches True.
  - **Analysis and closure rationale:** The `n` formatter uses locale grouping and separator settings. With `en_US.UTF-8`, `format(123456789, 'n')` now returns `'123,456,789'`, satisfying the reported grouping requirement.
  - **Related change:** [PR #7350](https://github.com/RustPython/RustPython/pull/7350): locale-aware numeric formatting.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/5181/README.md)

- **[#5656 — Not properly checking for invalid escape seqeunce \X](https://github.com/RustPython/RustPython/issues/5656)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'assert b"omkmok\Xaa" == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])'
  ```

  - **Before — [c3ed002b1204](https://github.com/RustPython/RustPython/commit/c3ed002b1204d9ff156b5192b634a4056101b255) (nearest pre-issue main revision; approximate baseline):** The assertion passes without the required invalid-escape warning.
  - **After:** The assertion passes and stderr contains SyntaxWarning for \X.
  - **Analysis and closure rationale:** Compilation detects invalid escapes in bytes literals and emits the corresponding warning. The original bytes assertion still passes and now emits the missing `SyntaxWarning` for `\X`, satisfying the report.
  - **Related change:** [PR #7164](https://github.com/RustPython/RustPython/pull/7164): invalid string and bytes escape warnings.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/5656/README.md)

- **[#6429 — `sysconfig.get_config_var('Py_GIL_DISABLED')` returns `None`](https://github.com/RustPython/RustPython/issues/6429)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'import sysconfig; print(repr(sysconfig.get_config_var("Py_GIL_DISABLED")), flush=True)'
  ```

  - **Before — [e227956a58f0](https://github.com/RustPython/RustPython/commit/e227956a58f0f072f8be177264e0fdc1b9280e8a) (nearest pre-issue main revision; approximate baseline):** Py_GIL_DISABLED is None.
  - **After:** Py_GIL_DISABLED is 1 on the tested POSIX build.
  - **Analysis and closure rationale:** Build-time configuration now defines `Py_GIL_DISABLED` as `1`. On POSIX/macOS, `sysconfig.get_config_var("Py_GIL_DISABLED")` returns `1`, resolving the reported missing configuration value.
  - **Related change:** [PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose `Py_GIL_DISABLED` in build-time variables.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/6429/README.md)

- **[#6790 — Support xz](https://github.com/RustPython/RustPython/issues/6790)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
  import unittest

  from test import support


  def dummy():
      pass


  selected = support.requires_lzma()(dummy)
  print("skip", getattr(selected, "__unittest_skip__", False))
  print("reason", getattr(selected, "__unittest_skip_why__", None))
  try:
      selected()
      print("invoked", "success")
  except unittest.SkipTest as exc:
      print("invoked", "SkipTest")
      print("skip_message", str(exc))
  '
  ```

  Use the matching RustPython standard library, including `test.support`, with lzma available. The function is actually invoked after applying the decorator.

  - **Before — [ed785e3d8689](https://github.com/RustPython/RustPython/commit/ed785e3d868966e2a5f7478632cabd5a630e6934) (source revision linked in the report):** The decorated function raises SkipTest: requires lzma.
  - **After:** skip False; reason None; invoked success.
  - **Analysis and closure rationale:** The unconditional `lzma = None` override was removed from `requires_lzma`. With the module available, `requires_lzma()(dummy)` now invokes the function successfully; the requested removal of the forced skip is complete.
  - **Related change:** [PR #7896](https://github.com/RustPython/RustPython/pull/7896): remove the unconditional lzma skip override.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/6790/README.md)

- **[#8052 — `type(...).__name__` is `'EllipsisType'` instead of `'ellipsis'`](https://github.com/RustPython/RustPython/issues/8052)**

  ```sh
  RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'print(type(...).__name__); print(repr(type(...)))'
  ```

  - **Before — [83fe92042112](https://github.com/RustPython/RustPython/commit/83fe92042112f9db89a70495b552ab433d77e751) (nearest pre-issue main revision; approximate baseline):** EllipsisType and <class 'EllipsisType'>.
  - **After:** ellipsis and <class 'ellipsis'>, matching CPython.
  - **Analysis and closure rationale:** The built-in type is now named `ellipsis`. The original query returns `ellipsis` and `<class 'ellipsis'>`, matching CPython and resolving both reported naming outputs.
  - **Related change:** [PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.
  - [Detailed comparison and execution evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/8052/README.md)

Related PRs identify matching source changes; exact first-fixing commits were not established by parent/commit execution comparisons.

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
