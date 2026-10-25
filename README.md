🐞 Python Debug Agent

A lightweight Python debugging tool that runs Python programs, detects errors, captures local variables when exceptions occur, and generates readable diagnostic reports.

✨ Features

- Runtime error detection: Identifies errors such as "ZeroDivisionError", "NameError", "TypeError", and "IndexError".
- Syntax error detection: Reports compilation errors with line and column information.
- Local variable capture: Records local variables from traceback frames when an exception occurs.
- Timeout handling: Stops programs that exceed the configured execution time.
- JSON reports: Provides structured output for automation and integrations.
- Static checks: Detects selected suspicious Python patterns without executing the program.
- Command-line interface: Run the debugger directly from your terminal.
- No mandatory API key: Core debugging works without an LLM service.

🛠️ Requirements

- Python 3.9 or newer
- Git
- VS Code or another Python editor

🚀 Installation

Clone the repository:

git clone https://github.com/YOUR-USERNAME/python-debug-agent.git
cd python-debug-agent

Create and activate a virtual environment on Windows:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

Install the project:

python -m pip install -e ".[dev]"

Replace "YOUR-USERNAME" with your GitHub username.

▶️ Usage

Run a Python file:

dbg examples/zero_division.py

Generate a JSON report:

dbg examples/zero_division.py --json

Run a program with a shorter timeout:

dbg examples/zero_division.py --timeout 2

Run a clean example:

dbg examples/clean.py

Run the test suite:

python -m pytest -v

You can also use the module directly:

python -m debug_agent examples/zero_division.py

🧪 Example

Consider this Python program:

def average(numbers):
    total = sum(numbers)
    return total / len(numbers)

print(average([]))

The program raises a "ZeroDivisionError" because the list is empty.

The Debug Agent can report the error type, traceback location, and available local variables to help you diagnose the problem.

📁 Project Structure

python-debug-agent/
├── debug_agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core.py
│   ├── cli.py
│   └── runner.py
├── examples/
│   ├── clean.py
│   └── zero_division.py
├── tests/
│   └── test_core.py
├── .gitignore
├── pyproject.toml
└── README.md

⚠️ Security and Limitations

- The subprocess runner is not a security sandbox.
- Executed programs may access files and resources using the current user's permissions.
- Timeouts help with programs that run too long but do not make untrusted code safe.
- Static checks identify selected patterns and cannot detect every logical bug.
- LLM-based explanations or automatic repairs are not included in the current implementation.

Never run untrusted Python code on a system containing sensitive information.

🧪 Testing

Run:

python -m pytest -v

Tests should pass before publishing changes. The number of passing tests depends on the current test suite.

📜 License

This project is intended to use the MIT License. Add a "LICENSE" file containing the official MIT license text before claiming that the repository is MIT-licensed.

🤝 Contributions

Issues, bug reports, and improvements are welcome.