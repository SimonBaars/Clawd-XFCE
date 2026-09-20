"""python -m clippy_xfce"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    if "--prepare" in args:
        from clippy_xfce.sprites import ensure_assets

        agent, frames, sounds = ensure_assets()
        print(f"Clippy ready: {len(agent.animations)} animations")
        print(f"frames: {frames}")
        print(f"sounds: {sounds}")
        return 0
    import clippy_xfce.gi_setup  # noqa: F401
    from clippy_xfce.app import main as app_main

    return app_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
