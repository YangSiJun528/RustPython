# #4784 — docs.rs page linked in the readme doesn't exist " rustpython-0.1.2 is not a library."

The README's docs.rs destination now serves published RustPython 0.6.0 API documentation. The linked API documentation is available, satisfying the original documentation-link report.

Original issue: [https://github.com/RustPython/RustPython/issues/4784](https://github.com/RustPython/RustPython/issues/4784)

## Reproduce locally

```sh
sh tools/issue-repros/cases/4784/check.sh
```

The response should be the RustPython API documentation after redirects. The recorded check served version 0.6.0. This command performs a read-only HTTP request.

## Recorded comparison

- Historical result: The reported docs destination did not provide the expected API documentation.
- Current result: The README destination serves RustPython 0.6.0 API documentation.
- [Recorded HTTP checks](evidence/http-checks.json).

## Related change

[Published API documentation](https://docs.rs/rustpython/latest/rustpython/).

AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.
