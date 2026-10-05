"""Render the current draft from imported verification data; run no interpreters."""

import json
from pathlib import Path


def render():
    root = Path(__file__).resolve().parent
    catalog = json.loads((root / "catalog.json").read_text())
    issues = catalog["issues"]
    resolved = [row for row in issues if row["closure_recommended"]]
    partial = [row for row in issues if not row["closure_recommended"]]
    assert len(resolved) == 24 and {row["issue"] for row in partial} == {
        4613,
        5181,
        6790,
    }
    url = "https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros"
    baseline = catalog["baseline"]
    draft = [
        "# Review 24 independently verified issues for closure",
        "",
        "I independently rechecked the reports below and found sufficient evidence that their reported problems are resolved. Could you review these results and close the corresponding issues?",
        "",
        f"Verification used [{baseline[:12]}](https://github.com/RustPython/RustPython/commit/{baseline}) on October 5, 2026. The fresh runs used macOS ARM64 and, for the explicitly identified slot B cases, x86_64 RustPython through Rosetta. CPython comparisons used 3.14.6 ARM64. The documentation-link case was checked against the actual served API content.",
        "",
        "The related changes explain the observed behavior; the exact first fixing commits were not established. Historical failure logs were reused, while the current results were independently executed. Each detailed report separates those evidence sources and states its limits.",
        "",
        "This is an unsubmitted issue-body draft. #4613, #5181 and #6790 remain partially resolved and are excluded from this closure request; see the [remaining issues](recheck/not-ready.md). #6697 is outside these independent audits and is not counted.",
        "",
    ]
    for row in resolved:
        number = row["issue"]
        draft.extend(
            [
                f"- **[#{number}](https://github.com/RustPython/RustPython/issues/{number}) — {row['title']}.**",
                "  " + row["result"],
                "  " + row["related"] + ".",
                "",
                f"  - [Reproduction and results]({url}/recheck/cases/{number}/README.md).",
                "",
            ]
        )
    draft.extend(
        [
            "AI assistance: verification, evidence packaging and drafting with OpenAI Codex.",
            "",
        ]
    )
    (root.parent / "report.md").write_text("\n".join(draft))
    remaining = [
        "# Partially resolved issues — not included in the closure request",
        "",
        "The baseline is the same f39b054b9c8c commit used for the 24 closure candidates. These are concrete remaining failures, not timeouts, missing locale prerequisites or failed builds.",
        "",
    ]
    for row in partial:
        number = row["issue"]
        remaining.extend(
            [
                f"## #{number} — {row['title']}",
                "",
                row["result"],
                "",
                row["limits"],
                "",
                f"[Reproducer, expected/current results and full evidence](cases/{number}/README.md).",
                "",
            ]
        )
    remaining.extend(
        [
            "The earlier 16-issue draft recommended closing #5181 and #6790; those recommendations are superseded by the independent review. The earlier additional-11 report recommended closing #4613; that recommendation is superseded too. No bug fix or issue submission is part of this report update.",
            "",
        ]
    )
    (root / "not-ready.md").write_text("\n".join(remaining))
    for row in issues:
        case = root / "cases" / str(row["issue"])
        case.mkdir(parents=True, exist_ok=True)
        (case / "README.md").write_text(row["case_document"])
    print(
        f"Rendered {len(resolved)} closure candidates and {len(partial)} partial cases."
    )


if __name__ == "__main__":
    render()
