# #4786 — Type name cannot contain surrogates

Original issue: [#4786](https://github.com/RustPython/RustPython/issues/4786)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'print(repr(type("A\udcdcB", (), {})))'
```

## Before and after

- **Before — [010640ccc8f7](https://github.com/RustPython/RustPython/commit/010640ccc8f74f56075df09a654352ae3d162d25) (nearest pre-issue main revision; approximate baseline):** Creates a type whose name contains a replacement character.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** UnicodeEncodeError rejects the surrogate in the name (expected exit 1).

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>&lt;class '__main__.A�B'&gt;</code></pre></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No other output</em><p><em>6 interpreter cleanup warning lines omitted.</em></p></td>
<td valign="top"><pre><code>UnicodeEncodeError: 'utf-8' codec can't encode character
'\udcdc' in position 1: surrogates not allowed</code></pre><p><em>4 traceback header/frame lines omitted.</em></p></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>0</code></td>
<td valign="top"><code>1</code></td>
</tr>
</tbody>
</table>

To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. The linked execution metadata records the historical build toolchain.

## Analysis and closure rationale

String literals preserve lone surrogates, and type-name validation rejects them. The original `type("A\udcdcB", (), {})` input now raises the expected `UnicodeEncodeError`, resolving the silent replacement-character behavior.

[PR #5629](https://github.com/RustPython/RustPython/pull/5629): preserve surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
