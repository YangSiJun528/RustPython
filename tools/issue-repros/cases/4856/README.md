# #4856 — Assertion failed: table.sub_tables.is_empty() when decorator class takes a lambda argument.

Original issue: [#4856](https://github.com/RustPython/RustPython/issues/4856)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

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

## Before and after

- **Before — [c7faae9b22ce](https://github.com/RustPython/RustPython/commit/c7faae9b22ce31a3ba1f2cc1cd3ad759b54ce100) (reported v0.2.0 release tag):** Compiler panic: table.sub_tables.is_empty().
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** compile_success (exit 0).

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>compile_success</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><pre><code>thread 'main' panicked at 'assertion failed:
table.sub_tables.is_empty()',
compiler/codegen/src/compile.rs:305:9
note: run with `RUST_BACKTRACE=1` environment variable to
display a backtrace</code></pre><p><em>6 interpreter cleanup warning lines omitted.</em></p></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>101</code></td>
<td valign="top"><code>0</code></td>
</tr>
</tbody>
</table>

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

Class decorators are scanned before entering the class scope, matching code-generation order and keeping nested symbol tables aligned. The original source now compiles without the reported `table.sub_tables.is_empty()` panic.

[PR #8138](https://github.com/RustPython/RustPython/pull/8138): correct class-decorator scope scanning order.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
