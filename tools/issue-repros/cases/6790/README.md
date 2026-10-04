# #6790 — Support xz

Original issue: [#6790](https://github.com/RustPython/RustPython/issues/6790)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

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

## Before and after

- **Before — [ed785e3d8689](https://github.com/RustPython/RustPython/commit/ed785e3d868966e2a5f7478632cabd5a630e6934) (source revision linked in the report):** The decorated function raises SkipTest: requires lzma.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** skip False; reason None; invoked success.

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>skip True
reason requires lzma
invoked SkipTest
skip_message requires lzma</code></pre></td>
<td valign="top"><pre><code>skip False
reason None
invoked success</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No other output</em><p><em>8 interpreter cleanup warning lines omitted.</em></p></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>0</code></td>
<td valign="top"><code>0</code></td>
</tr>
</tbody>
</table>

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

The unconditional `lzma = None` override was removed from `requires_lzma`. With the module available, `requires_lzma()(dummy)` now invokes the function successfully; the requested removal of the forced skip is complete.

[PR #7896](https://github.com/RustPython/RustPython/pull/7896): remove the unconditional lzma skip override.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
