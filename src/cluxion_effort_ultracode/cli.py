"""cluxion-ultracode CLI (skeleton; implementation lands via the build)."""

from __future__ import annotations

import json
import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("--version", "-V"):
        from cluxion_effort_ultracode import __version__

        print(f"cluxion-ultracode {__version__}")
        return 0
    print(json.dumps({"ok": False, "error": "not_implemented", "hint": "build in progress"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
