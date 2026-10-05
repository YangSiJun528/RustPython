# #8052 — `type(...).__name__` is `'EllipsisType'` instead of `'ellipsis'`

Original issue: [#8052](https://github.com/RustPython/RustPython/issues/8052)

**Verified closure candidate:** `type(...).__name__` and the type's repr now give `ellipsis` and `<class 'ellipsis'>`, matching CPython, in place of the previous `EllipsisType` spelling.

**Tested commits:** before `83fe92042112` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repro.py](repro.py). The original executable input is retained.

```python
print(type(...).__name__)
print(repr(type(...)))
```

## Expected and observed results

**Expected:** ellipsis and <class 'ellipsis'>, matching CPython.

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before</th><th>RustPython after</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>ellipsis
&lt;class 'ellipsis'&gt;</code></pre></td>
<td valign="top"><pre><code>EllipsisType
&lt;class 'EllipsisType'&gt;</code></pre></td>
<td valign="top"><pre><code>ellipsis
&lt;class 'ellipsis'&gt;</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><em>No output</em></td>
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

The built-in type is now named `ellipsis`. The original query returns `ellipsis` and `<class 'ellipsis'>`, matching CPython and resolving both reported naming outputs.

[PR #8580](https://github.com/RustPython/RustPython/pull/8580): correct the Ellipsis type name.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [83fe92042112](https://github.com/RustPython/RustPython/commit/83fe92042112f9db89a70495b552ab433d77e751) (nearest pre-issue main revision; approximate baseline).
- **After:** [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- **Platform:** macOS ARM64.
- **Rust toolchains:** before `rustc 1.99.0 (b940084d7 2026-09-28)`; after `rustc 1.99.0 (b940084d7 2026-09-28)`. Default Cargo features, committed lockfiles.
- **CPython:** `3.14.6 (main, Jun 23 2026, 15:46:31) [Clang 22.1.3 ]`. [Reference provenance](evidence/reference.json).
- **Full reproduction:** [BUILD.md](BUILD.md) contains exact checkout, toolchain, build and executable-version checks. Return to the Run section after setup.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).
- [CPython stdout](evidence/cpython.stdout.txt) / [CPython stderr](evidence/cpython.stderr.txt).
AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
