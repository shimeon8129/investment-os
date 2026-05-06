from pathlib import Path

from reporting.portfolio_candidate_review import (
    find_existing_candidate_file,
    generate_portfolio_candidate_review,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "docs" / "PORTFOLIO_CANDIDATE_REVIEW_SMOKE_TEST.md"


def main():
    candidate_path = find_existing_candidate_file()

    report_path = generate_portfolio_candidate_review(
        candidate_path=candidate_path,
        report_path=REPORT_PATH,
    )

    assert report_path.exists()

    content = report_path.read_text(encoding="utf-8")

    assert "# Portfolio vs Candidate Review" in content
    assert "## Summary" in content
    assert "## Review Buckets" in content
    assert "## Full Comparison Table" in content
    assert (
        "HELD_NOT_CANDIDATE" in content
        or "HELD_AND_CANDIDATE" in content
        or "CANDIDATE_NOT_HELD" in content
    )
    assert "汎銓" in content
    assert "泰鼎" not in content

    print(f"Candidate source: {candidate_path}")
    print(f"Smoke report generated: {report_path}")
    print("Portfolio candidate review smoke test passed.")


if __name__ == "__main__":
    main()
