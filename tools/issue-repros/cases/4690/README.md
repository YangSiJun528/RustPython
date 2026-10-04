# #4690 — classmethod_descriptor

Original issue: [#4690](https://github.com/RustPython/RustPython/issues/4690)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c 'print(type(dict.__dict__["fromkeys"]).__name__)'
```

## Before and after

- **Before — [8ff947e83a65](https://github.com/RustPython/RustPython/commit/8ff947e83a65b74c920edc63aed8a0a5854b8612) (nearest pre-issue main revision; approximate baseline):** Raw dict.fromkeys descriptor has type classmethod.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** Raw descriptor has type classmethod_descriptor.

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below. Only the first stdout line, from the raw descriptor query reproduced above, is shown.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>classmethod</code></pre></td>
<td valign="top"><pre><code>classmethod_descriptor</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No other output</em><p><em>6 interpreter cleanup warning lines omitted.</em></p></td>
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

Native class methods now use the dedicated `classmethod_descriptor` type. `dict.__dict__["fromkeys"]` has that type, matching CPython and resolving the reported descriptor-type mismatch.

[PR #8780](https://github.com/RustPython/RustPython/pull/8780): native class-method descriptor construction.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
