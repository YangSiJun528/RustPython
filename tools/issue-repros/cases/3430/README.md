# #3430 — etree.XML raises TypeError on valid XML

Original issue: [#3430](https://github.com/RustPython/RustPython/issues/3430)

**Verified closure candidate:** `etree.XML("<root></root>")` previously raised a `TypeError` for a `None` encoding. It now returns an empty `root` element; the parser accepts that encoding argument.

**Tested commits:** before `310578c422c9` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repro.py](repro.py). REPL prompts and traceback are excluded from executable input; the returned element type, tag, text and child count are printed.

```python
import xml.etree.ElementTree as etree

result = etree.XML("<root></root>")
print(type(result).__name__, result.tag, result.text, len(result))
```

## Expected and observed results

**Expected:** Element root None 0 (exit 0).

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before</th><th>RustPython after</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>Element root None 0</code></pre></td>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>Element root None 0</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>TypeError: Expected type 'str', not 'NoneType'</code></pre><p><em>12 interpreter cleanup warning lines omitted.</em></p><p><em>7 traceback header/frame lines omitted.</em></p></td>
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

The parser accepts the explicit `None` encoding argument passed by ElementTree. The original `etree.XML("<root></root>")` call now returns the expected empty root element, resolving the reported `TypeError`.

[PR #6582](https://github.com/RustPython/RustPython/pull/6582): accept `None` for the parser encoding; [PR #8741](https://github.com/RustPython/RustPython/pull/8741): native ElementTree parser implementation.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [310578c422c9](https://github.com/RustPython/RustPython/commit/310578c422c9b3d76eb8c739136b972d78e37180) (nearest pre-issue main revision; approximate baseline).
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
  File "<survey>/verification-tools/derived-transcripts/issue-3430-case-01/probe.py", line 2, in <module>
    result = etree.XML("<root></root>")
  File "<checkout>/vm/pylib-crate/Lib/xml/etree/ElementTree.py", line 1319, in XML
    parser = XMLParser(target=TreeBuilder())
  File "<checkout>/vm/pylib-crate/Lib/xml/etree/ElementTree.py", line 1508, in __init__
    parser = expat.ParserCreate(encoding, "}")
TypeError: Expected type 'str', not 'NoneType'
```

</details>

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
