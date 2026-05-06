from pathlib import Path

from reporting.candidate_review import (
    find_existing_candidates_file,
    generate_candidate_review_report,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "docs" / "CANDIDATE_REVIEW_SMOKE_TEST.md"


def main():
    candidates_path = find_existing_candidates_file()
    report_path = generate_candidate_review_report(
        candidates_path=candidates_path,
        report_path=REPORT_PATH,
    )

    assert report_path.exists()

    content = report_path.read_text(encoding="utf-8")

    assert "# Candidate Review Report" in content
    assert "## Summary" in content
    assert "## Candidate Review Table" in content
    assert "## Top Candidate Notes" in content
    assert "scanner_score" in content
    assert "raw_score" in content
    assert "raw_level" in content
    assert "raw_price" in content

    print(f"Candidate source: {candidates_path}")
    print(f"Smoke report generated: {report_path}")
    print("Candidate review smoke test passed.")


if __name__ == "__main__":
    main()
