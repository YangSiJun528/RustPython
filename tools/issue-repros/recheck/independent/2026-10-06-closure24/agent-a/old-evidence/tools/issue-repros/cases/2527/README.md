# #2527 — expressions in blocks don't print their value in the REPL

Original issue: [#2527](https://github.com/RustPython/RustPython/issues/2527)

**Verified closure candidate:** The original loop and `with` block previously displayed no expression values. They now display `0`–`9` and `5`, respectively, in the Linux REPL with `TERM=xterm`.

**Tested commits:** before `163cd1953377` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repl.txt](repl.txt). Both original blocks are retained. The /tmp/file.txt path is replaced by a file inside the runner scratch directory; exit() is appended after both blocks return to the primary prompt.

Enter the following in a real REPL, with a blank line after each indented block.

```python
for i in range(10):
    i

with open("repl-output.txt", "w") as f:
    f.write("hello")
```

## Expected and observed results

**Expected:** The loop displays 0 through 9; the with block displays 5.

The CPython 3.14.6 reference was recorded separately on macOS ARM64 on October 5; both RustPython runs were on Linux ARM64. The same block input was sent through a PTY in all three runs.

The table extracts the expression values from the recorded terminal session, in execution order. Startup text, prompts, echoed input and terminal control sequences are omitted. The PTY recording combines stdout and stderr; the full transcript is linked below.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before</th><th>RustPython after</th></tr></thead>
<tbody>
<tr>
<th>REPL expression output</th>
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
<td valign="top"><code>0</code></td>
</tr>
</tbody>
</table>

## Run

First complete [BUILD.md](BUILD.md) in the same shell. It creates `rustpython_repro_root`, builds both pinned commits and verifies their versions. Keep both checkouts while running these commands.

Run in a terminal with a TTY. For **each** interpreter, enter the input above, press Enter on an empty line after each indented block, then enter `exit()`. The loop starts historical first, then current. A script or piped stdin does not test interactive display.

```sh
for phase in historical current; do
  if [ "$phase" = historical ]; then
    rustpython_repro_image="$rustpython_repro_historical_image"
  else
    rustpython_repro_image="$rustpython_repro_current_image"
  fi
  printf "\n%s REPL\n" "$phase"
  mkdir -p "$rustpython_repro_root/scratch-$phase/config/rustpython"
  docker run --rm -it --platform linux/arm64 --network none \
    --mount "type=bind,source=$rustpython_repro_root/$phase,target=/repo,readonly" \
    --mount "type=bind,source=$rustpython_repro_root/target-$phase,target=/target,readonly" \
    --mount "type=bind,source=$rustpython_repro_root/scratch-$phase,target=/scratch" \
    --env TERM=xterm --env XDG_CONFIG_HOME=/scratch/config \
    --env RUSTPYTHONPATH=/repo/Lib --env PYTHONDONTWRITEBYTECODE=1 \
    --workdir /scratch "$rustpython_repro_image" /target/release/rustpython
done
```

For the CPython reference, start `PYTHON_BASIC_REPL=1 python3.14` in a disposable directory and enter the same blocks interactively. Record `python3.14 -VV` first.

## Analysis and closure rationale

Interactive compilation now emits expression output inside module-level blocks. The original loop displays 0–9 and the `with` block displays 5, resolving both missing-output examples on Linux with `TERM=xterm`.

[PR #7067](https://github.com/RustPython/RustPython/pull/7067): interactive expression handling in nested blocks.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [163cd1953377](https://github.com/RustPython/RustPython/commit/163cd1953377f4049e06fdae55c715889857a301) (nearest pre-issue main revision; approximate baseline).
- **After:** [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- **Platform:** Linux ARM64 (Docker).
- **Rust toolchains:** before `rustc 1.47.0 (18bf6b4f0 2020-10-07)`; after `rustc 1.99.0 (b940084d7 2026-09-28)`. Default Cargo features, committed lockfiles.
- **CPython:** `3.14.6 (main, Jun 23 2026, 15:46:31) [Clang 22.1.3 ]`. [Reference provenance](evidence/reference.json).
- **Full reproduction:** [BUILD.md](BUILD.md) contains exact checkout, toolchain, build and executable-version checks. Return to the Run section after setup.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [CPython stdout](evidence/cpython.stdout.txt) / [CPython stderr](evidence/cpython.stderr.txt).
AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
