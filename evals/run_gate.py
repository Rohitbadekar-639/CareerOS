"""M0-T19 eval-gate placeholder.

Offline eval on golden datasets becomes a real merge gate in M3/M9. Until then
this runner exists so CI can require the job and prove the wiring.
"""

from __future__ import annotations


def main() -> int:
    print("eval-gate: placeholder - no golden datasets yet; passing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
