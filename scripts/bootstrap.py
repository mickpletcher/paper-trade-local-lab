from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--constraint", "requirements.lock", "pip"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--constraint", "requirements.lock", "-e", ".[dev]"],
        cwd=repo,
        check=True,
    )
    if (repo / "package-lock.json").is_file():
        npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
        if npm is None:
            raise RuntimeError("Node validation dependencies are declared but npm is not installed")
        subprocess.run([npm, "ci"], cwd=repo, check=True)
    subprocess.run([sys.executable, "-m", "tradeforge.cli", "doctor"], cwd=repo, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
