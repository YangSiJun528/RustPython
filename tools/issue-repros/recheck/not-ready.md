# Partially resolved issues — not included in the closure request

The baseline is the same f39b054b9c8c commit used for the 25 closure candidates. These are concrete remaining failures, not timeouts, missing locale prerequisites or failed builds.

## #4613 — Locale support for FormatSpec n

Basic n and the original locale tests pass. Across five available locales, 395 formatting results include 102 differences: 84 zero-padding cases and 18 other Unicode-separator width cases.

The zero-padding defect was rerun on native ARM64 too. The fr_FR U+202F width counterexample was run with Rosetta RustPython; >20n produces 18 characters rather than 20.

[Reproducer, expected/current results and full evidence](cases/4613/README.md).

## #5181 — Locale-aware n formatting

Bare n and the original locale test pass, but en_US format(123456789, "015n") gives 0000123,456,789 instead of CPython's 000,123,456,789.

The locale exists and grouping is active. Both outputs have length 15; the defect is grouping, not missing locale setup.

[Reproducer, expected/current results and full evidence](cases/5181/README.md).

## #6790 — XZ support and the forced lzma skip

The forced skip is gone and basic XZ operations pass. However, identical CPython-generated XZ input returns 0 bytes from the first decompress(max_length=100) call in RustPython, versus 100 bytes in CPython.

The corresponding existing test is an expectedFailure, not a pass. Its marker was retained. The remaining concrete streaming defect prevents closure.

[Reproducer, expected/current results and full evidence](cases/6790/README.md).

The earlier 16-issue draft recommended closing #5181 and #6790; those recommendations are superseded by the independent review. The earlier additional-11 report recommended closing #4613; that recommendation is superseded too. No bug fix or issue submission is part of this report update.
