from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_license_names_project_author():
    license_text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")

    assert "Copyright (c) 2024 RepoDossier Developer" in license_text
    assert ("Repo" + "Context Authors") not in license_text
    assert "RepoDossier Authors" not in license_text


def test_public_project_support_files_exist():
    expected_files = [
        "CONTRIBUTING.md",
        "SECURITY.md",
        ".github/workflows/ci.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
    ]

    for relative_path in expected_files:
        assert (PROJECT_ROOT / relative_path).is_file(), relative_path


def test_contributing_documents_generated_exports_and_tests():
    text = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "python3 -m pytest --color=yes" in text
    assert "full.txt" in text
    assert "ai.txt" in text
    assert "docs.txt" in text
    assert "changed.txt" in text
    assert "Do not commit generated export files" in text


def test_security_policy_documents_private_reporting_and_export_scope():
    text = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")

    assert "Reporting a vulnerability" in text
    assert "Please do not disclose security vulnerabilities publicly" in text
    assert "Secret handling" in text
    assert "database contents are exported instead of schema metadata" in text


def test_readme_mentions_public_project_support():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Public project support" in text
    assert "CONTRIBUTING.md" in text
    assert "SECURITY.md" in text
    assert "GitHub Actions CI" in text
    assert "context-export" in text
