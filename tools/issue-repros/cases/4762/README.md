# #4762 — cformat star asterisk should behave differently when given negative sign

Negative dynamic widths now select left alignment. The original `'%*s' % (-5, 'abc') == 'abc  '` assertion passes, including the two trailing spaces.

Original issue: [https://github.com/RustPython/RustPython/issues/4762](https://github.com/RustPython/RustPython/issues/4762)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 4762
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
assert "%*s" % (-5, "abc") == "abc  "
```

The original executable input is retained.

## Recorded comparison

- Historical result: The negative-width assertion raises AssertionError.
- Current result: The assertion passes; two trailing spaces are retained.
- Historical revision: [c36e3612e7dd1c7abd9fc7b76b912372bd26afbf](https://github.com/RustPython/RustPython/commit/c36e3612e7dd1c7abd9fc7b76b912372bd26afbf).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #4766](https://github.com/RustPython/RustPython/pull/4766): preserve left alignment for negative dynamic widths.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
