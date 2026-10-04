# #5181 — `format()` does not support locales for 'n' presentation type

The `n` formatter uses locale grouping and separator settings. With `en_US.UTF-8`, `format(123456789, 'n')` now returns `'123,456,789'`, satisfying the reported grouping requirement.

Original issue: [https://github.com/RustPython/RustPython/issues/5181](https://github.com/RustPython/RustPython/issues/5181)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 5181
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
import locale

print("locale", locale.setlocale(locale.LC_ALL, "en_US.UTF-8"))
print("result", repr(format(123456789, "n")))
print("matches", format(123456789, "n") == "123,456,789")
```

The locale is explicitly set to en_US.UTF-8 and the original expression result is printed.

The system must provide the `en_US.UTF-8` locale (`locale -a`). A missing locale is a setup error.

## Recorded comparison

- Historical result: With en_US.UTF-8: result '123456789', matches False.
- Current result: With en_US.UTF-8: result '123,456,789', matches True.
- Historical revision: [a8ab7dd3881437ad2eef31b3470427db20656a84](https://github.com/RustPython/RustPython/commit/a8ab7dd3881437ad2eef31b3470427db20656a84).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #7350](https://github.com/RustPython/RustPython/pull/7350): locale-aware numeric formatting.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
