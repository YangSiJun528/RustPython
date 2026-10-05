# #3418 — Introduce `_collections.OrderedDict` type (a.k.a. `collections.OrderedDict`)

Original issue: [#3418](https://github.com/RustPython/RustPython/issues/3418)

**Verified closure candidate:** `from _collections import OrderedDict` previously raised `ImportError`. The native implementation is now exported and the import succeeds.

**Tested commits:** before `40fd9c2683d7` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repro.py](repro.py). The original executable input is retained.

```python
from _collections import OrderedDict
```

## Expected and observed results

**Expected:** The import succeeds (exit 0).

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before</th><th>RustPython after</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><em>No output</em></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>ImportError: cannot import name 'OrderedDict'</code></pre><p><em>12 interpreter cleanup warning lines omitted.</em></p><p><em>3 traceback header/frame lines omitted.</em></p></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>0</code></td>
<td valign="top"><code>1</code></td>
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

CPython reference (3.14.6 in the recorded comparison):

```sh
(
  cd "$rustpython_repro_root" || exit
  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE RUSTPYTHONPATH
  python3.14 -VV
  if PYTHONDONTWRITEBYTECODE=1 python3.14 "$rustpython_repro_root/repro.py"; then
    printf 'exit_code=0\n'
  else
    printf 'exit_code=%s\n' "$?"
  fi
)
```

To run the comparison and capture all outputs together, use the optional [comparison command](../../README.md#compare-both-revisions-at-once). Direct commands above do not require that runner.

## Analysis and closure rationale

A native `OrderedDict` is now exported from `_collections`. The requested `from _collections import OrderedDict` import succeeds, satisfying the reported missing-export issue.

[PR #8780](https://github.com/RustPython/RustPython/pull/8780): native `OrderedDict` implementation and export.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [40fd9c2683d7](https://github.com/RustPython/RustPython/commit/40fd9c2683d76adf2b9ed0d77c055e2d2514c27d) (nearest pre-issue main revision; approximate baseline).
- **After:** [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- **Platform:** macOS ARM64.
- **Rust toolchains:** before `rustc 1.56.1 (59eed8a2a 2021-11-01)`; after `rustc 1.99.0 (b940084d7 2026-09-28)`. Default Cargo features, committed lockfiles.
- **CPython:** `3.14.6 (main, Jun 23 2026, 15:46:31) [Clang 22.1.3 ]`. [Reference provenance](evidence/reference.json).
- **Full reproduction:** [BUILD.md](BUILD.md) contains exact checkout, toolchain, build and executable-version checks. Return to the Run section after setup.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).
- [CPython stdout](evidence/cpython.stdout.txt) / [CPython stderr](evidence/cpython.stderr.txt).

<details>
<summary>Full recorded stderr (including traceback frames)</summary>

**Historical:**

```text
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
[WARN  rustpython_vm::pyobjectrc] couldn't run __del__ method for object
Traceback (most recent call last):
  File "<survey>/repros/3418/issue-3418-case-01/source-01.py", line 1, in <module>
    from _collections  import OrderedDict
ImportError: cannot import name 'OrderedDict'
```

</details>

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
