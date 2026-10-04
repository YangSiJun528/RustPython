# #3430 — etree.XML raises TypeError on valid XML

Original issue: [#3430](https://github.com/RustPython/RustPython/issues/3430)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
import xml.etree.ElementTree as etree

result = etree.XML("<root></root>")
print(type(result).__name__, result.tag, result.text, len(result))
'
```

## Before and after

- **Before — [310578c422c9](https://github.com/RustPython/RustPython/commit/310578c422c9b3d76eb8c739136b972d78e37180) (nearest pre-issue main revision; approximate baseline):** TypeError: Expected type 'str', not 'NoneType'.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** Element root None 0 (exit 0).

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>Element root None 0</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><pre><code>TypeError: Expected type 'str', not 'NoneType'</code></pre><p><em>12 interpreter cleanup warning lines omitted.</em></p><p><em>7 traceback header/frame lines omitted.</em></p></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>1</code></td>
<td valign="top"><code>0</code></td>
</tr>
</tbody>
</table>

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

The parser accepts the explicit `None` encoding argument passed by ElementTree. The original `etree.XML("<root></root>")` call now returns the expected empty root element, resolving the reported `TypeError`.

[PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept `None` for the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parser implementation.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
