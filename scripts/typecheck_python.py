"""Run strict mypy on each Python package (M0-T17/T20).

Invoked as one package at a time so same-named test modules across apps do not
collide inside a single mypy process.
"""

from __future__ import annotations

import subprocess
import sys

PACKAGES = (
    "shared/platform",
    "shared/shared_kernel",
    "contexts/identity",
    "apps/api",
    "apps/worker",
)


def main() -> int:
    for package in PACKAGES:
        print(f"mypy {package}")
        result = subprocess.run(
            [sys.executable, "-m", "mypy", package],
            check=False,
        )
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
