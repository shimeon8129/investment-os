from pathlib import Path

from reporting.daily_decision_dashboard import generate_daily_decision_dashboard


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "docs" / "DAILY_DECISION_DASHBOARD_SMOKE_TEST.md"


def main():
    report_path = generate_daily_decision_dashboard(report_path=REPORT_PATH)

    assert report_path.exists()

    content = report_path.read_text(encoding="utf-8")

    assert "# Daily Decision Dashboard v0" in content
    assert "## 1. Market / Signal State" in content
    assert "## 2. Top Candidates" in content
    assert "## 3. Current Holdings" in content
    assert "## 4. Portfolio vs Candidate Buckets" in content
    assert "## 5. Risk Notes" in content
    assert "## 6. Manual Action Checklist" in content

    assert "汎銓" in content
    assert "泰鼎" not in content

    print(f"Smoke dashboard generated: {report_path}")
    print("Daily decision dashboard smoke test passed.")


if __name__ == "__main__":
    main()
