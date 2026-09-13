import pytest
from app.services.code_analyzer import analyze_single_file, analyze_line_counts

def test_analyze_line_counts():
    python_code = "import os\n# Comment line\ndef foo():\n    return 42\n"
    res = analyze_line_counts(python_code, "Python")
    assert res["lines_total"] == 4
    assert res["lines_comment"] == 1
    assert res["lines_code"] == 3

def test_analyze_single_file_python(tmp_path):
    f = tmp_path / "test_script.py"
    f.write_text("def add(a, b):\n    return a + b\n")
    res = analyze_single_file(f, "Python", "source")
    assert res["parse_status"] == "success"
    assert res["function_count"] == 1
    assert res["lines_total"] == 2
