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
    (root.parent / "report.md").write_text(catalog["issue_body"])
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
