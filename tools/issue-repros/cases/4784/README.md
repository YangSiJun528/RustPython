# #4784 — docs.rs page linked in the readme doesn't exist " rustpython-0.1.2 is not a library."

Original issue: [#4784](https://github.com/RustPython/RustPython/issues/4784)

## Reproduction procedure

```sh
curl --fail --location https://docs.rs/rustpython
```

Follow redirects and inspect the returned API documentation. The recorded response was the RustPython 0.6.0 API page.

## Before and after

- **Before — Original documentation-link report:** The reported docs destination did not provide the expected API documentation.
- **After — documentation checked October 4, 2026:** The README destination serves RustPython 0.6.0 API documentation.

## Analysis and closure rationale

The README's docs.rs destination now serves published RustPython 0.6.0 API documentation. The linked API documentation is available, satisfying the original documentation-link report.

[Published API documentation](https://docs.rs/rustpython/latest/rustpython/).

## Recorded evidence

- [HTTP checks](evidence/http-checks.json).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
