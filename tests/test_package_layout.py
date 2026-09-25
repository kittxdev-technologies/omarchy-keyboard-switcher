from conftest import ROOT


def test_python_project_has_test_layout():
    assert (ROOT / "pyproject.toml").is_file()
    assert (ROOT / ".gitignore").is_file()
    assert (ROOT / "tests" / "conftest.py").is_file()
