# #8052 — `type(...).__name__` is `'EllipsisType'` instead of `'ellipsis'`

The built-in type is now named `ellipsis`. The original query returns `ellipsis` and `<class 'ellipsis'>`, matching CPython and resolving both reported naming outputs.

Original issue: [https://github.com/RustPython/RustPython/issues/8052](https://github.com/RustPython/RustPython/issues/8052)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 8052
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
print(type(...).__name__)
print(repr(type(...)))
```

The original executable input is retained.

## Recorded comparison

- Historical result: EllipsisType and <class 'EllipsisType'>.
- Current result: ellipsis and <class 'ellipsis'>, matching CPython.
- Historical revision: [83fe92042112f9db89a70495b552ab433d77e751](https://github.com/RustPython/RustPython/commit/83fe92042112f9db89a70495b552ab433d77e751).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
