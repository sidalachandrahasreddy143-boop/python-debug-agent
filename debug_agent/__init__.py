"""Public API for Python Debug Agent."""

from .core import (
    DebugReport,
    auto_debug,
    debug,
    debug_file,
    explain_exception,
    run_code,
    static_check,
)

__all__ = [
    "DebugReport",
    "debug",
    "debug_file",
    "auto_debug",
    "run_code",
    "static_check",
    "explain_exception",
]

__version__ = "1.0.0"