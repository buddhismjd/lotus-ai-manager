from __future__ import annotations

from pathlib import Path

from tools.repository_health import (
    build_report,
    inspect_tracked_paths,
)


def test_repository_health_accepts_regular_project_files(
    tmp_path: Path,
) -> None:
    (tmp_path / "pytest.ini").write_text(
        """
[pytest]
testpaths = tests
norecursedirs =
    _backup*
""".strip(),
        encoding="utf-8",
    )

    report = build_report(
        project_root=tmp_path,
        tracked_paths=(
            "backend/main.py",
            "tests/test_bodhi_api.py",
            "tools/catalog_health.py",
            "sync_tilda.bat",
        ),
    )

    assert report.healthy is True
    assert report.issues == ()


def test_repository_health_detects_tracked_backup_files() -> None:
    issues = inspect_tracked_paths(
        (
            "_backup_migration_tools_2026-07-12/tests/test_old.py",
        )
    )

    assert len(issues) == 1
    assert issues[0].code == "tracked_backup"


def test_repository_health_detects_generated_python_files() -> None:
    issues = inspect_tracked_paths(
        (
            "tests/__pycache__/test_api.cpython-312.pyc",
        )
    )

    assert len(issues) == 1
    assert issues[0].code == "tracked_generated_directory"


def test_repository_health_detects_patch_scripts() -> None:
    issues = inspect_tracked_paths(("apply_temporary_fix.py",))

    assert len(issues) == 1
    assert issues[0].code == "tracked_temporary_file"


def test_repository_health_detects_database_artifacts() -> None:
    issues = inspect_tracked_paths(("data/lotus_ai.db",))

    assert len(issues) == 1
    assert issues[0].code == "tracked_temporary_file"


def test_current_repository_is_healthy() -> None:
    report = build_report()

    assert report.healthy is True, tuple(
        (issue.code, issue.path, issue.message)
        for issue in report.issues
    )
