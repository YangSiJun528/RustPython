# Disassembly support used by modulefinder (#3846)

Original issue: [#3846](https://github.com/RustPython/RustPython/issues/3846)

**Verified closure candidate:** The three requested dis APIs operate on actual bytecode. A five-module import graph and all 17 original ModuleFinderTest tests pass without skip or expectedFailure.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Run the shared [probes.py](../../evidence/additional11/agent-a/probes.py.txt) with selector `3846`, as shown in the recorded command. The relevant function is `issue3846`; the full file supplies its imports and dispatcher. The excerpt is formatted for readability.

<details>
<summary>Reproducer function: issue3846</summary>

```python
def issue3846():
    import dis, modulefinder, pathlib, tempfile, types

    source = "import first\nfrom package import second\nfrom package.second import value\ndef nested():\n    import nested_dependency\n"
    code = compile(source, "<independent-3846>", "exec")
    assert isinstance(dis.opmap["LOAD_CONST"], int)
    assert isinstance(dis.EXTENDED_ARG, int)
    instructions = list(dis._unpack_opargs(code.co_code))
    assert instructions and all(isinstance(x, tuple) for x in instructions)
    print("opmap, EXTENDED_ARG, _unpack_opargs: usable")
    root = pathlib.Path(tempfile.mkdtemp(prefix="modulefinder-"))
    (root / "package").mkdir()
    files = {
        "main.py": source,
        "first.py": "flag=True\n",
        "package/__init__.py": "from . import second\n",
        "package/second.py": "value=42\n",
        "nested_dependency.py": "x=1\n",
    }
    for name, content in files.items():
        with (root / name).open("x") as out:
            out.write(content)
    finder = modulefinder.ModuleFinder(path=[str(root)])
    finder.run_script(str(root / "main.py"))
    expected = ["__main__", "first", "nested_dependency", "package", "package.second"]
    assert sorted(finder.modules) == expected, sorted(finder.modules)
    assert finder.any_missing_maybe() == ([], [])
    print("module graph:", sorted(finder.modules))
    print("missing:", finder.any_missing_maybe())
```

</details>

## Expected and observed results

**Expected:** The requested dis exports and instruction iteration must support the reported modulefinder path.

**Observed:** The three requested dis APIs operate on actual bytecode. A five-module import graph and all 17 original ModuleFinderTest tests pass without skip or expectedFailure.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
opmap, EXTENDED_ARG, _unpack_opargs: usable
module graph: ['__main__', 'first', 'nested_dependency', 'package', 'package.second']
missing: ([], [])
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
opmap, EXTENDED_ARG, _unpack_opargs: usable
module graph: ['__main__', 'first', 'nested_dependency', 'package', 'package.second']
missing: ([], [])
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:** No output.

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
Traceback (most recent call last):
  File "<survey>/verification-tools/derived-a/issue-3846-case-01.py", line 2, in <module>
    print(repr(dis.opmap['LOAD_CONST']))
AttributeError: module 'dis' has no attribute 'opmap'
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B '<additional11-audit>/agent-a/probes.py' \
  3846
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<additional11-audit>/agent-a/probes.py' 3846
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

The three requested dis APIs operate on actual bytecode. A five-module import graph and all 17 original ModuleFinderTest tests pass without skip or expectedFailure.

[PR #5377](https://github.com/RustPython/RustPython/pull/5377): provide dis exports and bytecode/import scanning.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** Opcode numeric equality is not required. Creating a generator from integer 100 is not evidence of bytecode iteration; valid code bytes were iterated instead.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`5631d2102bfe`](https://github.com/RustPython/RustPython/commit/5631d2102bfeb8e0ace727ba539258beb6cdbb7e), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-5631d2102b-01-7f102daa-1ca15133.stdout](../../evidence/history/logs/issue-3846-case-01/historical-5631d2102b-01-7f102daa-1ca15133.stdout).
- [Full reused historical-5631d2102b-01-7f102daa-1ca15133.stderr](../../evidence/history/logs/issue-3846-case-01/historical-5631d2102b-01-7f102daa-1ca15133.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

- **[3846-cpython](../../evidence/additional11/agent-a/3846-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/3846-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/3846-cpython.stderr.txt).
- **[3846-rustpython](../../evidence/additional11/agent-a/3846-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/3846-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/3846-rustpython.stderr.txt).
- **[3846-unittest-rustpython](../../evidence/additional11/agent-a/3846-unittest-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/3846-unittest-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/3846-unittest-rustpython.stderr.txt).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
