# #3430 — etree.XML raises TypeError on valid XML

The parser accepts the explicit `None` encoding argument passed by ElementTree. The original `etree.XML("<root></root>")` call now returns the expected empty root element, resolving the reported `TypeError`.

Original issue: [https://github.com/RustPython/RustPython/issues/3430](https://github.com/RustPython/RustPython/issues/3430)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 3430
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
import xml.etree.ElementTree as etree

result = etree.XML("<root></root>")
print(type(result).__name__, result.tag, result.text, len(result))
```

REPL prompts and traceback are excluded from executable input; the returned element type, tag, text and child count are printed.

## Recorded comparison

- Historical result: TypeError: Expected type 'str', not 'NoneType'.
- Current result: Element root None 0 (exit 0).
- Historical revision: [310578c422c9b3d76eb8c739136b972d78e37180](https://github.com/RustPython/RustPython/commit/310578c422c9b3d76eb8c739136b972d78e37180).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept `None` for the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parser implementation.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
