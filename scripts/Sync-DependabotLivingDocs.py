from __future__ import annotations

import argparse
import re
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--dependency", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    today = datetime.now(UTC).date().isoformat()

    changelog = repo / "CHANGELOG.md"
    entry = (
        f"### Automated dependency synchronization: {args.dependency}\n\n"
        f"Summary: Refreshed the living project records for the trusted Dependabot update `{args.dependency}`.\n\n"
        "Why: Dependency changes must update current state before governance validation.\n\n"
    )
    content = changelog.read_text(encoding="utf-8")
    heading = f"## {today}\n\n"
    if heading in content:
        content = content.replace(heading, heading + entry, 1)
    else:
        content = content.replace("# Changelog\n\n", f"# Changelog\n\n{heading}{entry}", 1)
    changelog.write_text(content, encoding="utf-8")

    update_marker(repo / "ASSESSMENT.md", "dependabot-sync", args.dependency)
    update_marker(repo / "FUTURE-UPGRADES.md", "dependabot-sync", args.dependency)
    update_marker(repo / "COMPLETED-UPGRADES.md", "dependabot-sync", args.dependency)
    return 0


def update_marker(path: Path, name: str, value: str) -> None:
    content = path.read_text(encoding="utf-8")
    marker = f"<!-- {name}: {value} -->"
    pattern = rf"(?m)^<!-- {re.escape(name)}: .* -->$"
    content = re.sub(pattern, marker, content) if re.search(pattern, content) else content.rstrip() + f"\n\n{marker}\n"
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
