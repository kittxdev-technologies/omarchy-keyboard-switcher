import json
from types import SimpleNamespace

from keyboard_devices import apply_group, build_keyword_args, main, parse_enabled_value


def _write_event(root, event, name):
    path = root / "class" / "input" / event / "device" / "name"
    path.parent.mkdir(parents=True)
    path.write_text(name + "\n", encoding="utf-8")


def test_build_keyword_args_keeps_untrusted_name_in_one_argv_item():
    name = 'Keyboard ; touch /tmp/should-not-run'

    args = build_keyword_args(name, False)

    assert args == [
        "keyword",
        f"device[{name}]:enabled",
        "false",
    ]
    assert "sh" not in args


def test_apply_group_never_toggles_unclassified_devices():
    calls = []
    devices = [
        {"name": "Laptop", "event": "/dev/input/event1", "category": "internal", "enabled": True},
        {"name": "Touchpad", "event": "/dev/input/event2", "category": "unclassified", "enabled": True},
    ]

    result = apply_group(devices, "all", False, lambda args: calls.append(args))

    assert result == {"ok": True, "changed": ["Laptop"], "failed": []}
    assert len(calls) == 1
    assert "Touchpad" not in calls[0][1]


def test_apply_group_reports_partial_failure_without_claiming_success():
    devices = [
        {"name": "First", "event": "/dev/input/event1", "category": "bluetooth", "enabled": True},
        {"name": "Second", "event": "/dev/input/event2", "category": "bluetooth", "enabled": True},
    ]

    def runner(args):
        if "Second" in args[1]:
            raise RuntimeError("hyprctl failed")

    result = apply_group(devices, "bluetooth", False, runner)

    assert result["ok"] is False
    assert result["changed"] == ["First"]
    assert result["failed"] == ["Second"]


def test_parse_enabled_option_accepts_hyprland_json_shapes():
    assert parse_enabled_value({"int": 1, "set": True}) is True
    assert parse_enabled_value({"int": 0, "set": True}) is False
    assert parse_enabled_value({"str": "true", "set": True}) is True
    assert parse_enabled_value({"set": False}) is True
    assert parse_enabled_value({"set": True, "str": "unknown"}) is None


def test_list_command_emits_live_device_json(tmp_path, capsys):
    name = "Built-in keyboard"
    _write_event(tmp_path, "event3", name)

    def runner(args, **kwargs):
        if args[-1] == "devices":
            return SimpleNamespace(returncode=0, stdout=json.dumps({"keyboards": [{"name": name}]}), stderr="")
        if args[0] == "/fake/udevadm":
            return SimpleNamespace(returncode=0, stdout="ID_BUS=isa\nID_INPUT_KEYBOARD=1\n", stderr="")
        if args[2] == "getoption":
            return SimpleNamespace(returncode=0, stdout=json.dumps({"set": False}), stderr="")
        raise AssertionError(args)

    assert main(
        ["list"],
        hyprctl_path="/fake/hyprctl",
        udevadm_path="/fake/udevadm",
        sysfs_root=tmp_path,
        command_runner=runner,
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["devices"][0]["enabled"] is True
