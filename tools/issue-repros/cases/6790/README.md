# #6790 — Support xz

Original issue: [#6790](https://github.com/RustPython/RustPython/issues/6790)

**Verified closure candidate:** The unconditional `lzma = None` override has been removed. With lzma available, `requires_lzma()(dummy)` now invokes the function instead of raising `SkipTest`, satisfying the requested removal of the forced skip.

**Tested commits:** before `ed785e3d8689` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repro.py](repro.py). A derived probe applies requires_lzma()(dummy), then invokes the wrapped function and records whether it skips.

```python
import unittest

from test import support


def dummy():
    pass


selected = support.requires_lzma()(dummy)
print("skip", getattr(selected, "__unittest_skip__", False))
print("reason", getattr(selected, "__unittest_skip_why__", None))
try:
    selected()
    print("invoked", "success")
except unittest.SkipTest as exc:
    print("invoked", "SkipTest")
    print("skip_message", str(exc))
```

## Expected and observed results

**Expected:** skip False; reason None; invoked success.

This checks RustPython's `test.support.requires_lzma` gate with lzma available. No CPython column is used: the reported defect is RustPython's forced skip. Successful invocation does not establish complete XZ support.

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>RustPython before</th><th>RustPython after</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>skip True
reason requires lzma
invoked SkipTest
skip_message requires lzma</code></pre></td>
<td valign="top"><pre><code>skip False
reason None
invoked success</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No other output</em><p><em>8 interpreter cleanup warning lines omitted.</em></p></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>0</code></td>
<td valign="top"><code>0</code></td>
</tr>
</tbody>
</table>

## Run

First complete [BUILD.md](BUILD.md) in the same shell. It creates `rustpython_repro_root`, builds both pinned commits and verifies their versions. Keep both checkouts while running these commands.

Save the code above as `$rustpython_repro_root/repro.py` (or copy the linked `repro.py` there). Both versions execute this one file, each with its matching standard library:

```sh
(
  cd "$rustpython_repro_root" || exit
  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE
  for phase in historical current; do
    printf "\n%s\n" "$phase"
    if RUSTPYTHONPATH="$rustpython_repro_root/$phase/Lib" PYTHONDONTWRITEBYTECODE=1 \
      "$rustpython_repro_root/target-$phase/release/rustpython" \
      "$rustpython_repro_root/repro.py"; then
      printf 'exit_code=0\n'
    else
      printf 'exit_code=%s\n' "$?"
    fi
  done
)
```

To run the comparison and capture all outputs together, use the optional [comparison command](../../README.md#compare-both-revisions-at-once). Direct commands above do not require that runner.

## Analysis and closure rationale

The unconditional `lzma = None` override was removed from `requires_lzma`. With the module available, `requires_lzma()(dummy)` now invokes the function successfully; the requested removal of the forced skip is complete.

[PR #7896](https://github.com/RustPython/RustPython/pull/7896): remove the unconditional lzma skip override.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [ed785e3d8689](https://github.com/RustPython/RustPython/commit/ed785e3d868966e2a5f7478632cabd5a630e6934) (source revision linked in the report).
- **After:** [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- **Platform:** macOS ARM64.
- **Rust toolchains:** before `rustc 1.96.1 (31fca3adb 2026-06-26)`; after `rustc 1.99.0 (b940084d7 2026-09-28)`. Default Cargo features, committed lockfiles.
- **Full reproduction:** [BUILD.md](BUILD.md) contains exact checkout, toolchain, build and executable-version checks. Return to the Run section after setup.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

<details>
<summary>Full recorded stderr (including traceback frames)</summary>

**Historical:**

```text
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:59:02Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
```

</details>

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
