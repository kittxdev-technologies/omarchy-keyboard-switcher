from conftest import ROOT


def test_publication_files_and_commands_are_documented():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

    assert "omarchy plugin add" in readme
    assert "omarchy plugin remove" in readme
    assert "Restore safe defaults" in readme
    assert "Esc" in readme and "Caps Lock" in readme
    assert "unsandboxed" in security
    assert "sudo" in security
    assert (ROOT / "LICENSE").is_file()
    assert (ROOT / "preview.png").is_file()

