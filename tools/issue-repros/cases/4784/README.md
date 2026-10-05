# #4784 — docs.rs page linked in the readme doesn't exist " rustpython-0.1.2 is not a library."

Original issue: [#4784](https://github.com/RustPython/RustPython/issues/4784)

**Verified closure candidate:** The linked docs.rs page previously reported that `rustpython-0.1.2` was not a library. The README destination now serves the published RustPython 0.6.0 API documentation.

## Expected and observed results

**Expected:** the README link opens published RustPython API documentation.

- **Before (original report):** The reported docs destination did not provide the expected API documentation.
- **After (checked October 4, 2026):** The README destination serves RustPython 0.6.0 API documentation.
- The recorded request followed redirects to `https://docs.rs/rustpython/latest/rustpython/` (HTTP 200). The page content was checked separately from the HTTP status.
- CPython and interpreter build comparisons do not apply to this documentation-link issue.

## Run

```sh
curl --fail --location https://docs.rs/rustpython
```

Follow redirects and inspect the API page. An HTTP 200 response alone is insufficient: the old crate landing page also returns 200.

## Analysis and closure rationale

The README's docs.rs destination now serves published RustPython 0.6.0 API documentation. The linked API documentation is available, satisfying the original documentation-link report.

[Published API documentation](https://docs.rs/rustpython/latest/rustpython/).

## Recorded evidence

- [HTTP checks](evidence/http-checks.json).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
