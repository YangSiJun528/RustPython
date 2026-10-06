# Email Subject with an unknown encoding (#4937)

[Original issue](https://github.com/RustPython/RustPython/issues/4937). **Resolved in the reported scope.** The original X-encoded Subject is returned without KeyError. Unknown encodings and related malformed-header controls were also checked.

## Environment

- Source and standard library: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Verified October 5, 2026 on macOS 26.5.2 ARM64.
- RustPython: 0.6.1, Python 3.14.0.alpha; native ARM64.
- Comparison: CPython 3.14.6 ARM64.

Use absolute paths for the variables below:

- `RP`: the RustPython executable for this commit.
- `CP`: the CPython 3.14.6 executable.
- `SRC`: the source directory at this commit, including its matching `Lib`.
- `CASE`: the directory containing the files shown below.

Shell variables replace recorded absolute paths. Export them so the Python inputs can use them:

```sh
export RP CP SRC CASE
unset PYTHONPATH PYTHONHOME PYTHONWARNINGS PYTHONSTARTUP
export PYTHONDONTWRITEBYTECODE=1
```

## Reproducer

Save as `4937-original.py`.

```python
import email
import email.policy

mytext = "Subject:=?us-ascii?X?value?="
em = email.message_from_string(mytext, policy=email.policy.default)
em.get("Subject")
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/4937-original.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/4937-original.py"
```

## Results

**Expected:** Retrieving the reported Subject must recover from the unknown encoded-word encoding.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

No output.

**stderr:**

No output.

### Historical failure

Previously recorded at [`02840593bc56`](https://github.com/RustPython/RustPython/commit/02840593bc56ae416ba2646166628f1712d6cf43); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

**stderr:**

```text
    kwds['parse_tree'] = cls.value_parser(value)
  File "<historical-checkout>/pylib/Lib/email/_header_value_parser.py", line 1498, in get_unstructured
    pass
  File "<historical-checkout>/pylib/Lib/email/_header_value_parser.py", line 1494, in get_unstructured
    token, value = get_encoded_word(value)
  File "<historical-checkout>/pylib/Lib/email/_header_value_parser.py", line 1447, in get_encoded_word
    "encoded word format invalid: '{}'".format(ew.cte))
  File "<historical-checkout>/pylib/Lib/email/_header_value_parser.py", line 1444, in get_encoded_word
    text, charset, lang, defects = _ew.decode('=?' + tok + '?=')
  File "<historical-checkout>/pylib/Lib/email/_encoded_words.py", line 166, in decode
    bstring, defects = _cte_decoders[cte](bstring)
KeyError: x
```

## Related change and scope

[PR #5663](https://github.com/RustPython/RustPython/pull/5663): unknown encoded-word recovery.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-a/4937-original-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-a/4937-original-rp.json).
- [Executed source](../../evidence/initial16/agent-a/4937-original.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/4937/evidence/metadata.json).

AI assistance: OpenAI Codex.
