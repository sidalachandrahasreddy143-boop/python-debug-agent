"""Child-process runner for Python Debug Agent.

This module is reserved for future structured runtime diagnostics.
The current core engine executes code in a subprocess directly.
"""

def main() -> int:
    print(
        "The standalone runner is not implemented yet. "
        "Use the main CLI: python -m debug_agent"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())