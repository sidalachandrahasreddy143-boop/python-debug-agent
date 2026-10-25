"""Command-line interface for Python Debug Agent."""

import argparse
import json
import sys
from pathlib import Path

from .core import debug, debug_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dbg",
        description="Run Python code and explain errors.",
    )

    parser.add_argument(
        "path",
        nargs="?",
        help="Python file or directory to debug. Use '-' to read code from stdin.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="python-debug-agent 1.0.0",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="Execution timeout in seconds (default: 10).",
    )
    parser.add_argument(
        "--stdin",
        default="",
        help="Text supplied to input() in the program.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output when the program succeeds.",
    )
    parser.add_argument(
        "--no-static",
        action="store_true",
        help="Skip static AST checks.",
    )
    parser.add_argument(
        "--vscode",
        action="store_true",
        help="Print a compact file:line:column diagnostic.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.path:
        parser.error("please provide a Python file, directory, or '-'")

    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    path = args.path

    if path == "-":
        code = sys.stdin.read()
        report = debug(
            code,
            filename="<stdin>",
            timeout=args.timeout,
            stdin_text=args.stdin,
        )
    else:
        source_path = Path(path)

        if source_path.is_dir():
            reports = []
            for file_path in sorted(source_path.rglob("*.py")):
                result = debug_file(
                    str(file_path),
                    timeout=args.timeout,
                )
                reports.append(result)

            if args.json:
                print(json.dumps([r.to_dict() for r in reports], indent=2))
            else:
                for result in reports:
                    if not (args.quiet and result.ok):
                        result.show()

            return 1 if any(not r.ok for r in reports) else 0

        report = debug_file(
            str(source_path),
            timeout=args.timeout,
        )

    if args.no_static:
        report.warnings = []

    if args.json:
        print(report.to_json())
    elif args.vscode and not report.ok:
        line = report.line or 1
        column = report.column or 1
        print(
            f"{report.filename}:{line}:{column}: "
            f"error: {report.error_type or report.status}: {report.message}"
        )
    elif not (args.quiet and report.ok):
        report.show()

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())