import json

from conftest import ROOT


def test_manifest_declares_a_namespaced_single_bar_widget():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schemaVersion"] == 1
    assert manifest["id"] == "io.github.dev.keyboard-switcher"
    assert not manifest["id"].startswith("omarchy.")
    assert manifest["kinds"] == ["bar-widget"]
    assert manifest["entryPoints"]["barWidget"] == "BarWidget.qml"
    assert manifest["barWidget"]["allowMultiple"] is False


def test_device_service_uses_fixed_helper_and_group_names_only():
    source = (ROOT / "DeviceService.qml").read_text(encoding="utf-8")

    assert "keyboard-devices" in source
    assert '"set-group"' in source
    assert '"internal"' in source
    assert '"bluetooth"' in source
    assert "bash" not in source
    assert "sh -c" not in source


def test_panel_contains_mouse_recovery_controls():
    source = (ROOT / "Panel.qml").read_text(encoding="utf-8")

    assert "Built-in keyboard" in source
    assert "Bluetooth keyboards" in source
    assert "Restore safe defaults" in source
    assert "MouseArea" in source


def test_publish_files_exist():
    required = {"manifest.json", "BarWidget.qml", "Panel.qml", "DeviceService.qml", "Model.js"}
    assert required <= {path.name for path in ROOT.iterdir()}

