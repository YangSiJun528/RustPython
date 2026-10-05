# README API documentation link (#4784)

Original issue: [#4784](https://github.com/RustPython/RustPython/issues/4784)

**Verified closure candidate:** The README destination returned HTTP 200 and an actual RustPython 0.6.0 API page, including crate and API content; status alone was not the oracle.

**README source:** [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). The external documentation destination was checked on October 5, 2026.

## Reproducer

This is an HTTP destination/content check. No Python interpreter comparison applies.

## Expected and observed results

**Expected:** The README link must serve API documentation rather than an error or generic page.

**Observed:** The README destination returned HTTP 200 and an actual RustPython 0.6.0 API page, including crate and API content; status alone was not the oracle.

This compares the reported documentation-link failure with the retrieved page. A CPython comparison does not apply.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
status=200
url=https://docs.rs/rustpython/latest/rustpython/
```

**stderr:**

```text
curl progress meter only (captured in tool transcript, not a separate file)
```

</details>

### Reported failure

The original report described a destination that did not provide API documentation. See the [preserved report](../../../cases/4784/README.md) for the earlier link and observations.

## Run

The recorded HTTP command follows. Local output paths use the [documented placeholders](../../ENVIRONMENT.md); substitute new scratch paths before replaying it.

```sh
curl --location --max-time 30 --output '<initial16-audit>/agent-b/fresh-4784-docs.html' \
  --dump-header '<initial16-audit>/agent-b/fresh-4784-headers.txt' --write-out \
  'status=%{http_code}\nurl=%{url_effective}\n' https://docs.rs/rustpython
```

The execution record links the requested URL, final destination, HTTP status and hashes of the saved body and headers.

## Analysis and closure rationale

The README destination returned HTTP 200 and an actual RustPython 0.6.0 API page, including crate and API content; status alone was not the oracle.

[Published API documentation](https://docs.rs/rustpython/latest/rustpython/).

**Scope and limitations:** This is the externally served page observed on October 5, 2026, not a documentation build from the baseline commit. CPython comparison does not apply.

## Environment

The HTTP request ran on macOS 26.5.2. No Python interpreter or CPython comparison was involved. The returned page identifies RustPython 0.6.0.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4784/README.md).
- [Independent assessment, original scope and limitations](assessment.json).

- **[fresh-4784-http](../../evidence/initial16/agent-b/fresh-4784-http.json)** — exit `0`; timeout `false`.
  stdout: in JSON / noted there; stderr: in JSON / noted there.

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
