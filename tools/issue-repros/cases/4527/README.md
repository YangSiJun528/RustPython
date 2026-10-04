# #4527 — top level objects are not deleted before script finalized

Shutdown now clears `__main__` globals while the facilities needed by finalizers remain available. The original global object's `__del__` prints `deleted!` during shutdown, satisfying the reported finalization behavior.

Original issue: [https://github.com/RustPython/RustPython/issues/4527](https://github.com/RustPython/RustPython/issues/4527)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 4527
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
class X:
    def __del__(self):
        print("deleted!")


x = X()
```

The original executable input is retained.

## Recorded comparison

- Historical result: No finalizer output at process shutdown.
- Current result: deleted! is printed at shutdown (exit 0).
- Historical revision: [e5735cde67b86699bd68c8959167ecf2649a6f2d](https://github.com/RustPython/RustPython/commit/e5735cde67b86699bd68c8959167ecf2649a6f2d).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: nearest pre-issue main revision; an approximation of the original environment.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #6934](https://github.com/RustPython/RustPython/pull/6934): module finalization during interpreter shutdown.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
