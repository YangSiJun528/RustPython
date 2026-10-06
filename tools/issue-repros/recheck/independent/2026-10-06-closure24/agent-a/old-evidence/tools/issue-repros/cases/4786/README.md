# #4786 — Type name cannot contain surrogates

Original issue: [#4786](https://github.com/RustPython/RustPython/issues/4786)

**Verified closure candidate:** `type("A\udcdcB", (), {})` previously created a class with a replacement character. It now raises the expected `UnicodeEncodeError`: the literal preserves the surrogate and type-name validation rejects it.

**Tested commits:** before `010640ccc8f7` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repro.py](repro.py.txt). The transcript expression is wrapped in print(repr(...)) to expose a wrongly accepted type; the correct outcome is an uncaught UnicodeEncodeError.

```python
print(repr(type("A\udcdcB", (), {})))
```

## Expected and observed results

**Expected:** UnicodeEncodeError rejects the surrogate in the name (expected exit 1).

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before</th><th>RustPython after</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>&lt;class '__main__.A�B'&gt;</code></pre></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><pre><code>UnicodeEncodeError: 'utf-8' codec can't encode character
'\udcdc' in position 1: surrogates not allowed</code></pre><p><em>4 traceback header/frame lines omitted.</em></p></td>
<td valign="top"><em>No other output</em><p><em>6 interpreter cleanup warning lines omitted.</em></p></td>
<td valign="top"><pre><code>UnicodeEncodeError: 'utf-8' codec can't encode character
'\udcdc' in position 1: surrogates not allowed</code></pre><p><em>4 traceback header/frame lines omitted.</em></p></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>1</code></td>
<td valign="top"><code>0</code></td>
<td valign="top"><code>1</code></td>
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

To run the comparison and capture all outputs together, use the optional [comparison command](../../../../../../../../archive/README-before-independent-review.md#compare-both-revisions-at-once). Direct commands above do not require that runner.

## Analysis and closure rationale

String literals preserve lone surrogates, and type-name validation rejects them. The original `type("A\udcdcB", (), {})` input now raises the expected `UnicodeEncodeError`, resolving the silent replacement-character behavior.

[PR #5629](https://github.com/RustPython/RustPython/pull/5629): preserve surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [010640ccc8f7](https://github.com/RustPython/RustPython/commit/010640ccc8f74f56075df09a654352ae3d162d25) (nearest pre-issue main revision; approximate baseline).
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

**CPython:**

```text
Traceback (most recent call last):
  File "<survey>/verification-tools/derived-transcripts/issue-4786-case-01/probe.py", line 1, in <module>
    print(repr(type("A\udcdcB", (), {})))
               ~~~~^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcdc' in position 1: surrogates not allowed
```

**Historical:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
```

**Current:**

```text
Traceback (most recent call last):
  File "<survey>/verification-tools/derived-transcripts/issue-4786-case-01/probe.py", line 1, in <module>
    print(repr(type("A\udcdcB", (), {})))
               ~~~~^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcdc' in position 1: surrogates not allowed
```

</details>

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
