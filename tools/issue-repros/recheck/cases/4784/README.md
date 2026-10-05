# README API documentation link (#4784)

[Original issue](https://github.com/RustPython/RustPython/issues/4784). **Resolved for the checked destination.** The README link serves RustPython API documentation.

## Check

The README source was [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). The external destination was checked on October 5, 2026 from macOS 26.5.2.

Set `CASE` to a directory for the response body and headers, then run:

```sh
curl --location --max-time 30 \
  --output "$CASE/docs.html" \
  --dump-header "$CASE/headers.txt" \
  --write-out 'status=%{http_code}\nurl=%{url_effective}\n' \
  https://docs.rs/rustpython
```

## Expected and observed results

The destination must contain RustPython API documentation. HTTP success alone is insufficient.

The request exited `0` and reported:

```text
status=200
url=https://docs.rs/rustpython/latest/rustpython/
```

The saved page identifies version **0.6.0**, has title **rustpython - Rust**, and its main heading is **Crate rustpython**. The body contains the crate documentation and API entries. The only stderr output was curl's progress meter.

The original issue described a destination that did not provide API documentation.

## Scope

This verifies the externally served documentation page at the recorded date. It is not a documentation build from `f39b054b9c8c`, and no CPython comparison applies.

## Evidence

- [HTTP command, status, redirect target and content hashes](../../evidence/initial16/agent-b/fresh-4784-http.json).
- [Saved response body](../../evidence/initial16/agent-b/fresh-4784-docs.html).
- [Saved response headers](../../evidence/initial16/agent-b/fresh-4784-headers.txt).
- [Scope assessment](assessment.json).
- [Historical report](../../../cases/4784/README.md).

AI assistance: OpenAI Codex.
