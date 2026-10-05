# #5181 — `format()` does not support locales for 'n' presentation type

Original issue: [#5181](https://github.com/RustPython/RustPython/issues/5181)

**Verified closure candidate:** With `en_US.UTF-8` selected, `format(123456789, 'n')` now returns `'123,456,789'` instead of `'123456789'`, using the locale's grouping and separator.

**Tested commits:** before `a8ab7dd38814` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repro.py](repro.py). The locale is explicitly set to en_US.UTF-8 and the original expression result is printed.

Requires the `en_US.UTF-8` system locale (`locale -a`).

```python
import locale

print("locale", locale.setlocale(locale.LC_ALL, "en_US.UTF-8"))
print("result", repr(format(123456789, "n")))
print("matches", format(123456789, "n") == "123,456,789")
```

## Expected and observed results

**Expected:** With en_US.UTF-8: result '123,456,789', matches True.

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before</th><th>RustPython after</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>locale en_US.UTF-8
result '123,456,789'
matches True</code></pre></td>
<td valign="top"><pre><code>locale en_US.UTF-8
result '123456789'
matches False</code></pre></td>
<td valign="top"><pre><code>locale en_US.UTF-8
result '123,456,789'
matches True</code></pre></td>
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

The `n` formatter uses locale grouping and separator settings. With `en_US.UTF-8`, `format(123456789, 'n')` now returns `'123,456,789'`, satisfying the reported grouping requirement.

[PR #7350](https://github.com/RustPython/RustPython/pull/7350): locale-aware numeric formatting.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [a8ab7dd38814](https://github.com/RustPython/RustPython/commit/a8ab7dd3881437ad2eef31b3470427db20656a84) (nearest pre-issue main revision; approximate baseline).
- **After:** [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- **Platform:** macOS ARM64.
- **Rust toolchains:** before `rustc 1.75.0 (82e1608df 2023-12-21)`; after `rustc 1.99.0 (b940084d7 2026-09-28)`. Default Cargo features, committed lockfiles.
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
```

</details>

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
