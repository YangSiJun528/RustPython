# #2527 — expressions in blocks don't print their value in the REPL

Interactive compilation now emits expression output inside module-level blocks. The original loop displays 0–9 and the `with` block displays 5, resolving both missing-output examples on Linux with `TERM=xterm`.

Original issue: [https://github.com/RustPython/RustPython/issues/2527](https://github.com/RustPython/RustPython/issues/2527)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 2527
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Use Linux with a working PTY. The runner sets `TERM=xterm` and waits for each prompt. To check manually, paste the following blocks into the RustPython REPL, including the blank line after each block:

Input: [repl.txt](repl.txt)

```python
for i in range(10):
    i

with open("repl-output.txt", "w") as f:
    f.write("hello")
```

Both original blocks are retained. The /tmp/file.txt path is replaced by a file inside the runner scratch directory; exit() is appended after both blocks return to the primary prompt.

## Recorded comparison

- Historical result: Neither block displayed its expression values.
- Current result: The loop displays 0 through 9; the with block displays 5.
- Historical revision: [163cd1953377f4049e06fdae55c715889857a301](https://github.com/RustPython/RustPython/commit/163cd1953377f4049e06fdae55c715889857a301).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: Linux ARM64, TERM=xterm.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).

## Related change

[PR #7067](https://github.com/RustPython/RustPython/pull/7067): interactive expression handling in nested blocks.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
