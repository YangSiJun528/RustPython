# #4527 — top level objects are not deleted before script finalized

Original issue: [#4527](https://github.com/RustPython/RustPython/issues/4527)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
class X:
    def __del__(self):
        print("deleted!")


x = X()
'
```

## Before and after

- **Before — [e5735cde67b8](https://github.com/RustPython/RustPython/commit/e5735cde67b86699bd68c8959167ecf2649a6f2d) (nearest pre-issue main revision; approximate baseline):** No finalizer output at process shutdown.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** deleted! is printed at shutdown (exit 0).

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>deleted!</code></pre></td>
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

Shutdown now clears `__main__` globals while the facilities needed by finalizers remain available. The original global object's `__del__` prints `deleted!` during shutdown, satisfying the reported finalization behavior.

[PR #6934](https://github.com/RustPython/RustPython/pull/6934): module finalization during interpreter shutdown.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
