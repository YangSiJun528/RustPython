# #4762 — cformat star asterisk should behave differently when given negative sign

Original issue: [#4762](https://github.com/RustPython/RustPython/issues/4762)

**Verified closure candidate:** The original `'%*s' % (-5, 'abc') == 'abc  '` assertion now passes. Negative width selects left alignment, including the required two trailing spaces.

**Tested commits:** before `c36e3612e7dd` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repro.py](repro.py). The original executable input is retained.

```python
assert "%*s" % (-5, "abc") == "abc  "
```

## Expected and observed results

**Expected:** The assertion passes; two trailing spaces are retained.

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
<td valign="top"><pre><code>AssertionError</code></pre><p><em>6 interpreter cleanup warning lines omitted.</em></p><p><em>3 traceback header/frame lines omitted.</em></p></td>
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

Negative dynamic widths now select left alignment. The original `'%*s' % (-5, 'abc') == 'abc  '` assertion passes, including the two trailing spaces.

[PR #4766](https://github.com/RustPython/RustPython/pull/4766): preserve left alignment for negative dynamic widths.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [c36e3612e7dd](https://github.com/RustPython/RustPython/commit/c36e3612e7dd1c7abd9fc7b76b912372bd26afbf) (nearest pre-issue main revision; approximate baseline).
- **After:** [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- **Platform:** macOS ARM64.
- **Rust toolchains:** before `rustc 1.67.1 (d5a82bbd2 2023-02-07)`; after `rustc 1.99.0 (b940084d7 2026-09-28)`. Default Cargo features, committed lockfiles.
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
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
Traceback (most recent call last):
  File "<survey>/repros/4762/issue-4762-case-01/source-01.py", line 1, in <module>
    assert('%*s' % (-5, 'abc') == 'abc  ')
AssertionError
```

</details>

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
