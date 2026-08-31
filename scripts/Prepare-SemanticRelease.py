from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True, order=True, slots=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "Version":
        match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value.strip())
        if match is None:
            raise ValueError(f"Invalid semantic version: {value}")
        return cls(*(int(part) for part in match.groups()))

    def bump(self, level: str) -> "Version":
        if level == "major":
            return Version(self.major + 1, 0, 0)
        if level == "minor":
            return Version(self.major, self.minor + 1, 0)
        if level == "patch":
            return Version(self.major, self.minor, self.patch + 1)
        raise ValueError(f"Unsupported release level: {level}")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--output")
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    current = _project_version(root / "pyproject.toml")
    latest_tag = _latest_release_tag(root)
    if latest_tag is None or current > latest_tag:
        action = "tag"
        level = "none"
        next_version = current
    else:
        level = _release_level(_commit_subjects(root, f"v{latest_tag}"))
        action = "bump" if level != "none" else "none"
        next_version = current.bump(level) if action == "bump" else current
    payload = {
        "action": action,
        "current_version": str(current),
        "latest_tag": None if latest_tag is None else str(latest_tag),
        "level": level,
        "next_version": str(next_version),
        "tag": f"v{next_version}",
    }
    if arguments.prepare:
        if action != "bump":
            raise RuntimeError("A semantic version bump is not currently required.")
        _prepare_release_files(root, next_version)
    if arguments.output:
        output = Path(arguments.output)
        with output.open("a", encoding="utf-8", newline="\n") as stream:
            for key, value in payload.items():
                stream.write(f"{key}={'' if value is None else value}\n")
    print(json.dumps(payload, indent=2))
    return 0


def _project_version(path: Path) -> Version:
    match = re.search(r'(?m)^version = "(?P<version>\d+\.\d+\.\d+)"$', path.read_text(encoding="utf-8"))
    if match is None:
        raise RuntimeError("pyproject.toml has no supported project version.")
    return Version.parse(match.group("version"))


def _latest_release_tag(root: Path) -> Version | None:
    result = subprocess.run(
        ["git", "tag", "--list", "v[0-9]*.[0-9]*.[0-9]*", "--sort=-v:refname"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    first = next((line for line in result.stdout.splitlines() if line.strip()), None)
    return None if first is None else Version.parse(first)


def _commit_subjects(root: Path, revision: str) -> list[str]:
    result = subprocess.run(
        ["git", "log", f"{revision}..HEAD", "--format=%s%n%b%x00"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [item.strip() for item in result.stdout.split("\x00") if item.strip()]


def _release_level(commits: list[str]) -> str:
    level = "none"
    for commit in commits:
        first_line = commit.splitlines()[0]
        if "BREAKING CHANGE:" in commit or re.match(r"^[a-z]+(?:\([^)]*\))?!:", first_line):
            return "major"
        if first_line.startswith("feat") and re.match(r"^feat(?:\([^)]*\))?:", first_line):
            level = "minor"
        elif level == "none" and re.match(r"^(fix|perf)(?:\([^)]*\))?:", first_line):
            level = "patch"
    return level


def _prepare_release_files(root: Path, version: Version) -> None:
    version_text = str(version)
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        re.sub(
            r'(?m)^version = "\d+\.\d+\.\d+"$', f'version = "{version_text}"', pyproject.read_text(encoding="utf-8")
        ),
        encoding="utf-8",
        newline="\n",
    )
    today = date.today().isoformat()
    changelog = root / "CHANGELOG.md"
    changelog.write_text(
        _insert_dated_entry(
            changelog.read_text(encoding="utf-8"),
            today,
            f"### Prepared semantic release v{version_text}\n\nSummary: Updated package and project records for v{version_text}.\n\nWhy: Conventional changes require one validated, reviewable release version before tag publication.\n",
        ),
        encoding="utf-8",
        newline="\n",
    )
    assessment = root / "ASSESSMENT.md"
    assessment_text = re.sub(
        r"(?m)^(?:Current package version|Version): .*\n", "", assessment.read_text(encoding="utf-8")
    )
    assessment.write_text(
        assessment_text.replace(
            "## Build And Dependencies\n", f"## Build And Dependencies\n\nVersion: {version_text}.\n", 1
        ),
        encoding="utf-8",
        newline="\n",
    )
    future = root / "FUTURE-UPGRADES.md"
    future_text = re.sub(r"(?m)^Current release baseline: .*\n", "", future.read_text(encoding="utf-8"))
    future.write_text(
        future_text.replace(
            "# Future Upgrades\n", f"# Future Upgrades\n\nCurrent release baseline: v{version_text}.\n", 1
        ),
        encoding="utf-8",
        newline="\n",
    )
    completed = root / "COMPLETED-UPGRADES.md"
    completed.write_text(
        _insert_dated_entry(
            completed.read_text(encoding="utf-8"), today, f"* Prepared semantic release v{version_text}.\n"
        ),
        encoding="utf-8",
        newline="\n",
    )


def _insert_dated_entry(content: str, day: str, entry: str) -> str:
    heading = f"## {day}\n"
    if heading in content:
        return content.replace(heading, f"{heading}\n{entry}", 1)
    first_break = content.find("\n")
    return f"{content[: first_break + 1]}\n{heading}\n{entry}{content[first_break + 1 :]}"


if __name__ == "__main__":
    raise SystemExit(main())
