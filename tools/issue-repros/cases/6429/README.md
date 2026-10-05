# #6429 — `sysconfig.get_config_var('Py_GIL_DISABLED')` returns `None`

Original issue: [#6429](https://github.com/RustPython/RustPython/issues/6429)

**Verified closure candidate:** `sysconfig.get_config_var('Py_GIL_DISABLED')` now returns `1` instead of `None` on the tested POSIX/macOS build. The value is defined in the build-time configuration.

**Tested commits:** before `e227956a58f0` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repro.py](repro.py). The missing import is supplied and the queried value is printed.

```python
import sysconfig

print(repr(sysconfig.get_config_var("Py_GIL_DISABLED")), flush=True)
```

## Expected and observed results

**Expected:** Py_GIL_DISABLED is 1 on the tested POSIX build.

CPython's recorded GIL-enabled build reports `0`; the RustPython POSIX build reports `1`. This is a build-configuration check: equality with CPython is not the oracle, and this probe does not establish general free-threading compatibility.

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before</th><th>RustPython after</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>0</code></pre></td>
<td valign="top"><pre><code>None</code></pre></td>
<td valign="top"><pre><code>1</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><em>No other output</em><p><em>6 interpreter cleanup warning lines omitted.</em></p></td>
<td valign="top"><em>No output</em></td>
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

Build-time configuration now defines `Py_GIL_DISABLED` as `1`. On POSIX/macOS, `sysconfig.get_config_var("Py_GIL_DISABLED")` returns `1`, resolving the reported missing configuration value.

[PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose `Py_GIL_DISABLED` in build-time variables.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [e227956a58f0](https://github.com/RustPython/RustPython/commit/e227956a58f0f072f8be177264e0fdc1b9280e8a) (nearest pre-issue main revision; approximate baseline).
- **After:** [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- **Platform:** macOS ARM64.
- **Rust toolchains:** before `rustc 1.96.1 (31fca3adb 2026-06-26)`; after `rustc 1.99.0 (b940084d7 2026-09-28)`. Default Cargo features, committed lockfiles.
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
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:31:05Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
```

</details>

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
