# #4937 — email.message_from_string.get() fails parses the special text

Unknown encoded-word encodings are handled by the email parser's invalid-input recovery. Retrieving the original X-encoded Subject now completes without the reported `KeyError: x`.

Original issue: [https://github.com/RustPython/RustPython/issues/4937](https://github.com/RustPython/RustPython/issues/4937)

## Reproduce locally

Build from the repository root with `cargo build --release --locked`, then run:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 4937
```

The Python 3 host script launches the supplied RustPython executable in a temporary directory. It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.

Input: [repro.py](repro.py)

```python
import email
import email.policy

mytext = "Subject:=?us-ascii?X?value?="
em = email.message_from_string(mytext, policy=email.policy.default)
em.get("Subject")
```

The original executable input is retained.

## Recorded comparison

- Historical result: Subject retrieval raises KeyError: x.
- Current result: The same retrieval completes (exit 0).
- Historical revision: [02840593bc56ae416ba2646166628f1712d6cf43](https://github.com/RustPython/RustPython/commit/02840593bc56ae416ba2646166628f1712d6cf43).
- Current revision: [f39b054b9c8cbbf884f53123eef028131789990c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Environment: macOS 26.5.2 ARM64; default-feature release builds.
- Baseline selection: a revision identified in the original report.
- [Execution metadata and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

## Related change

[PR #5663](https://github.com/RustPython/RustPython/pull/5663): email update that handles unknown encoded-word encodings.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
