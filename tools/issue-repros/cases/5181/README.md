# #5181 — `format()` does not support locales for 'n' presentation type

Original issue: [#5181](https://github.com/RustPython/RustPython/issues/5181)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

```sh
RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython -c '
import locale

print("locale", locale.setlocale(locale.LC_ALL, "en_US.UTF-8"))
print("result", repr(format(123456789, "n")))
print("matches", format(123456789, "n") == "123,456,789")
'
```

The system must provide `en_US.UTF-8` (`locale -a`). The command selects that locale explicitly.

## Before and after

- **Before — [a8ab7dd38814](https://github.com/RustPython/RustPython/commit/a8ab7dd3881437ad2eef31b3470427db20656a84) (nearest pre-issue main revision; approximate baseline):** With en_US.UTF-8: result '123456789', matches False.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** With en_US.UTF-8: result '123,456,789', matches True.

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>locale en_US.UTF-8
result '123456789'
matches False</code></pre></td>
<td valign="top"><pre><code>locale en_US.UTF-8
result '123,456,789'
matches True</code></pre></td>
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

The `n` formatter uses locale grouping and separator settings. With `en_US.UTF-8`, `format(123456789, 'n')` now returns `'123,456,789'`, satisfying the reported grouping requirement.

[PR #7350](https://github.com/RustPython/RustPython/pull/7350): locale-aware numeric formatting.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
