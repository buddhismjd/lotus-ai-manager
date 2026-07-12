from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_DIRECTORY_PREFIXES = (
    "_backup",
    "backup",
    "archive",
)

FORBIDDEN_FILE_PATTERNS = (
    "apply_*.py",
    "*.pyc",
    "*.pyo",
    "*.db",
    "*.db-shm",
    "*.db-wal",
)

FORBIDDEN_PATH_PARTS = (
    "__pycache__",
    ".pytest_cache",
)

REQUIRED_PYTEST_SETTINGS = {
    "testpaths": "tests",
    "norecursedirs": "_backup",
}


@dataclass(frozen=True)
class HealthIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class RepositoryHealthReport:
    healthy: bool
    tracked_files_checked: int
    issues: tuple[HealthIssue, ...]


def _run_git_ls_files(project_root: Path = PROJECT_ROOT) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return tuple(
        line.strip().replace("\\", "/")
        for line in completed.stdout.splitlines()
        if line.strip()
    )


def _has_forbidden_directory(path: Path) -> bool:
    for part in path.parts:
        normalized = part.lower()
        if any(
            normalized.startswith(prefix)
            for prefix in FORBIDDEN_DIRECTORY_PREFIXES
        ):
            return True
    return False


def _matches_forbidden_file_pattern(path: Path) -> bool:
    return any(path.match(pattern) for pattern in FORBIDDEN_FILE_PATTERNS)


def inspect_tracked_paths(paths: Iterable[str]) -> tuple[HealthIssue, ...]:
    issues: list[HealthIssue] = []

    for raw_path in paths:
        normalized_path = raw_path.replace("\\", "/")
        path = Path(normalized_path)

        if _has_forbidden_directory(path):
            issues.append(
                HealthIssue(
                    code="tracked_backup",
                    path=normalized_path,
                    message="Backup or archive content is tracked by Git.",
                )
            )
            continue

        if any(part in FORBIDDEN_PATH_PARTS for part in path.parts):
            issues.append(
                HealthIssue(
                    code="tracked_generated_directory",
                    path=normalized_path,
                    message="Generated Python or pytest content is tracked by Git.",
                )
            )
            continue

        if _matches_forbidden_file_pattern(path):
            issues.append(
                HealthIssue(
                    code="tracked_temporary_file",
                    path=normalized_path,
                    message="Temporary, database, or patch artifact is tracked by Git.",
                )
            )

    return tuple(issues)


def inspect_pytest_configuration(
    project_root: Path = PROJECT_ROOT,
) -> tuple[HealthIssue, ...]:
    config_path = project_root / "pytest.ini"

    if not config_path.is_file():
        return (
            HealthIssue(
                code="missing_pytest_config",
                path="pytest.ini",
                message="pytest.ini is missing.",
            ),
        )

    content = config_path.read_text(encoding="utf-8-sig")
    normalized = " ".join(content.lower().split())

    issues: list[HealthIssue] = []

    for setting, expected_fragment in REQUIRED_PYTEST_SETTINGS.items():
        if setting.lower() not in normalized or expected_fragment.lower() not in normalized:
            issues.append(
                HealthIssue(
                    code="invalid_pytest_config",
                    path="pytest.ini",
                    message=(
                        f"Required pytest setting is missing: "
                        f"{setting} -> {expected_fragment}"
                    ),
                )
            )

    return tuple(issues)


def build_report(
    project_root: Path = PROJECT_ROOT,
    tracked_paths: Sequence[str] | None = None,
) -> RepositoryHealthReport:
    resolved_paths = (
        tuple(tracked_paths)
        if tracked_paths is not None
        else _run_git_ls_files(project_root)
    )

    issues = (
        *inspect_tracked_paths(resolved_paths),
        *inspect_pytest_configuration(project_root),
    )

    return RepositoryHealthReport(
        healthy=not issues,
        tracked_files_checked=len(resolved_paths),
        issues=tuple(issues),
    )


def render_text_report(report: RepositoryHealthReport) -> str:
    status = "HEALTHY" if report.healthy else "ISSUES FOUND"

    lines = [
        "AI Bodhi Repository Health",
        f"Status: {status}",
        f"Tracked files checked: {report.tracked_files_checked}",
        f"Issues: {len(report.issues)}",
    ]

    for issue in report.issues:
        lines.append(
            f"- [{issue.code}] {issue.path}: {issue.message}"
        )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check AI Bodhi repository hygiene."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the repository health report as JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()

    if args.json:
        print(
            json.dumps(
                asdict(report),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(render_text_report(report))

    return 0 if report.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
