"""Allow running the package with python -m debug_agent."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())