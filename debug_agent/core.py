"""Core debugging engine for Python Debug Agent."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DebugReport:
    filename: str
    status: str
    error_type: str | None = None
    message: str = ""
    line: int | None = None
    column: int | None = None
    source: str = ""
    values: list[str] = field(default_factory=list)
    call_chain: list[str] = field(default_factory=list)
    what: str = ""
    why: str = ""
    fixes: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    @property
    def func(self) -> str | None:
        return self.call_chain[-1] if self.call_chain else None

    def show(self) -> None:
        print("=" * 60)
        print(f"DEBUG AGENT REPORT -> {self.filename}")
        print("=" * 60)
        print(f"STATUS : {self.status.upper()}")
        if self.error_type:
            print(f"ERROR  : {self.error_type}: {self.message}")
        if self.line:
            print(f"WHERE  : line {self.line}, column {self.column or 1}")
        if self.source:
            print(f"\n{self.line or '?'} | {self.source}")
        if self.what:
            print(f"\nWHAT HAPPENED\n{self.what}")
        if self.why:
            print(f"\nWHY IT HAPPENED\n{self.why}")
        if self.values:
            print("\nLOCAL VALUES")
            for value in self.values:
                print(f"  {value}")
        if self.fixes:
            print("\nPOSSIBLE FIXES")
            for fix in self.fixes:
                print(f"  - {fix}")
        if self.warnings:
            print("\nSTATIC WARNINGS")
            for warning in self.warnings:
                print(f"  - {warning}")
        if self.stdout:
            print("\nPROGRAM OUTPUT")
            print(self.stdout, end="" if self.stdout.endswith("\n") else "\n")
        if self.stderr:
            print("\nPROGRAM STDERR")
            print(self.stderr, end="" if self.stderr.endswith("\n") else "\n")
        print("=" * 60)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def static_check(code: str) -> list[str]:
    """Perform basic AST checks without executing the supplied program."""
    warnings: list[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return warnings

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    warnings.append(
                        f"Line {node.lineno}: mutable default argument in "
                        f"function '{node.name}'."
                    )

        if isinstance(node, ast.ExceptHandler) and node.type is None:
            warnings.append(
                f"Line {node.lineno}: bare 'except:' catches almost every exception."
            )

        if (
            isinstance(node, ast.ExceptHandler)
            and isinstance(node.body, list)
            and len(node.body) == 1
            and isinstance(node.body[0], ast.Pass)
        ):
            warnings.append(
                f"Line {node.lineno}: exception is silently ignored with 'pass'."
            )

        if (
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Constant)
            and node.left.value is None
            and any(isinstance(op, ast.Eq) for op in node.ops)
        ):
            warnings.append(
                f"Line {node.lineno}: use 'is None' instead of '== None'."
            )

    return list(dict.fromkeys(warnings))


def explain_exception(error: BaseException, code: str) -> DebugReport:
    """Explain an exception that has already been captured."""
    frames = traceback.extract_tb(error.__traceback__)
    frame = frames[-1] if frames else None

    line = frame.lineno if frame else None
    source = frame.line or "" if frame else ""
    filename = frame.filename if frame else "<unknown>"

    return DebugReport(
        filename=filename,
        status="error",
        error_type=type(error).__name__,
        message=str(error),
        line=line,
        source=source,
        what=f"Python raised {type(error).__name__}: {error}",
        why="Inspect the traceback and the values used at the failing line.",
        fixes=["Review the failing expression and validate its inputs."],
        call_chain=[f"{f.name} (line {f.lineno})" for f in frames],
    )


def debug(
    code: str,
    filename: str = "demo.py",
    timeout: float = 10,
    stdin_text: str = "",
    show: bool = False,
) -> DebugReport:
    """Run code in a separate Python process and return a diagnostic report."""
    report = DebugReport(filename=filename, status="ok")
    report.warnings = static_check(code)

    try:
        compile(code, filename, "exec")
    except (SyntaxError, IndentationError, TabError) as exc:
        report.status = "error"
        report.error_type = type(exc).__name__
        report.message = exc.msg
        report.line = exc.lineno
        report.column = exc.offset
        report.source = exc.text.strip() if exc.text else ""
        report.what = "Python could not compile the program."
        report.why = exc.msg
        report.fixes = ["Correct the syntax at the reported line and try again."]
        report.exit_code = 1
        if show:
            report.show()
        return report

    # Run the user's code in a child process, not inside this Python process.
    # This is process isolation for crash/timeout handling, NOT a security sandbox.
    with tempfile.TemporaryDirectory(prefix="python_debug_agent_") as temp_dir:
        script_path = Path(temp_dir) / "program.py"
        script_path.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(script_path)],
                input=stdin_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(0.1, float(timeout)),
                cwd=temp_dir,
                env={
                    **os.environ,
                    "PYTHONIOENCODING": "utf-8",
                },
            )
            report.stdout = result.stdout
            report.stderr = result.stderr
            report.exit_code = result.returncode

            if result.returncode != 0:
                report.status = "error"
                report.error_type, report.message, report.line, report.call_chain = (
                    _parse_traceback(result.stderr)
                )
                report.what = (
                    f"The program exited with code {result.returncode}."
                )
                report.why = report.message or "The program returned a non-zero exit code."
                report.fixes = [
                    "Read the traceback and inspect the reported line.",
                    "Check the input values and types used by that expression.",
                ]
                report.source = _source_at(code, report.line)

        except subprocess.TimeoutExpired:
            report.status = "timeout"
            report.error_type = "TimeoutError"
            report.message = f"Program exceeded the {timeout}-second time limit."
            report.what = "The program did not finish before the timeout."
            report.why = (
                "It may contain an infinite loop, wait for input, or perform a "
                "long-running operation."
            )
            report.fixes = [
                "Check loop termination conditions.",
                "Provide input through stdin_text if the program calls input().",
                "Increase the timeout if the computation is expected to take longer.",
            ]
            report.exit_code = 1

    if show:
        report.show()
    return report


def _parse_traceback(
    stderr: str,
) -> tuple[str | None, str, int | None, list[str]]:
    lines = stderr.strip().splitlines()
    error_type = None
    message = stderr.strip()
    line_number = None
    call_chain: list[str] = []

    for text in lines:
        if text.lstrip().startswith("File ") and ", line " in text:
            try:
                location = text.split(", line ", 1)[1]
                number = location.split(",", 1)[0]
                line_number = int(number)
                function = location.split('in ', 1)[-1].strip().strip('"')
                call_chain.append(f"{function} (line {line_number})")
            except (ValueError, IndexError):
                pass

    if lines:
        last = lines[-1]
        if ":" in last:
            error_type, message = last.split(":", 1)
            error_type = error_type.strip()
            message = message.strip()

    return error_type, message, line_number, call_chain


def _source_at(code: str, line: int | None) -> str:
    if line is None:
        return ""
    lines = code.splitlines()
    return lines[line - 1] if 1 <= line <= len(lines) else ""


def debug_file(path: str, timeout: float = 10, show: bool = False) -> DebugReport:
    """Debug a Python source file."""
    file_path = Path(path)
    if not file_path.is_file():
        return DebugReport(
            filename=str(file_path),
            status="harness-error",
            error_type="FileNotFoundError",
            message=f"File not found: {file_path}",
            what="The requested source file does not exist.",
            exit_code=2,
        )

    try:
        code = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return DebugReport(
            filename=str(file_path),
            status="harness-error",
            error_type=type(exc).__name__,
            message=str(exc),
            exit_code=2,
        )

    return debug(code, filename=str(file_path), timeout=timeout, show=show)


def run_code(code: str, timeout: float = 10) -> DebugReport:
    """Run code and return the report without printing it."""
    return debug(code, timeout=timeout, show=False)


def auto_debug(
    code: str,
    max_rounds: int = 3,
    use_llm: bool = False,
) -> DebugReport:
    """Run code and report the result.

    Automatic AI patching is not implemented in this initial version.
    """
    if use_llm:
        report = debug(code)
        report.hints.append(
            "LLM patching is not implemented in this version; no automatic edits were made."
        )
        return report

    return debug(code)