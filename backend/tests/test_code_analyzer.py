from pathlib import Path
from app.services.code_analyzer import analyze_single_file, analyze_line_counts

def test_analyze_line_counts():
    content = "# Header comment\ndef foo():\n    # Inside comment\n    return 42\n"
    counts = analyze_line_counts(content, "Python")
    assert counts["lines_total"] == 4
    assert counts["lines_comment"] == 2
    assert counts["lines_code"] == 2
    assert counts["lines_blank"] == 0

def test_analyze_python_ast(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    code = "class SampleService:\n    def __init__(self):\n        self.value = 10\n\n    def calculate(self, x):\n        if x > 10:\n            return x * 2\n        else:\n            return x + 1\n"
    py_file.write_text(code)
    
    res = analyze_single_file(py_file, "Python", "source")
    
    assert res["parse_status"] == "success"
    assert res["class_count"] == 1
    assert res["function_count"] == 2
    assert res["lines_total"] == 9
    assert res["average_complexity"] >= 1.0

def test_partial_failure_resilience(tmp_path: Path):
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text("def broken_syntax(x: return")
    
    res = analyze_single_file(invalid_file, "Python", "source")
    
    # Must NOT crash, must record parse_status='failed'
    assert res["parse_status"] == "failed"
    assert res["error_message"] is not None
