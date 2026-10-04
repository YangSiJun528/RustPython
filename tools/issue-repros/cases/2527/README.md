# #2527 — expressions in blocks don't print their value in the REPL

Original issue: [#2527](https://github.com/RustPython/RustPython/issues/2527)

## Reproduction procedure

Run from a RustPython checkout of the revision being tested. The recorded current revision is [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Build its default-feature release interpreter:

```sh
cargo build --release --locked
```

The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.

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

## Before and after

- **Before — [163cd1953377](https://github.com/RustPython/RustPython/commit/163cd1953377f4049e06fdae55c715889857a301) (nearest pre-issue main revision; approximate baseline):** Neither block displayed its expression values.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** The loop displays 0 through 9; the with block displays 5.

The table extracts the expression values from the recorded terminal session, in execution order. Startup text, prompts, echoed input and terminal control sequences are omitted. The PTY recording combines stdout and stderr; the full transcript is linked below.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>REPL expression output</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>0
1
2
3
4
5
6
7
8
9
5</code></pre></td>
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

Interactive compilation now emits expression output inside module-level blocks. The original loop displays 0–9 and the `with` block displays 5, resolving both missing-output examples on Linux with `TERM=xterm`.

[PR #7067](https://github.com/RustPython/RustPython/pull/7067): interactive expression handling in nested blocks.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
