from debug_agent import debug


def test_detects_zero_division():
    report = debug("print(10 / 0)")
    assert report.ok is False
    assert report.error_type == "ZeroDivisionError"


def test_valid_program_runs():
    report = debug("print('Hello World')")
    assert report.ok is True
    assert "Hello World" in report.stdout


def test_detects_syntax_error():
    report = debug("if True print('hello')")
    assert report.ok is False
    assert report.error_type == "SyntaxError"


def test_detects_timeout():
    report = debug("while True: pass", timeout=1)
    assert report.status == "timeout"