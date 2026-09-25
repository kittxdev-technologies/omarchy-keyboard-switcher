import json
from pathlib import Path

from keyboard_devices import discover, group_state


def _write_event(root: Path, event: str, name: str) -> None:
    path = root / "class" / "input" / event / "device" / "name"
    path.parent.mkdir(parents=True)
    path.write_text(name + "\n", encoding="utf-8")


def _hypr(*names: str) -> str:
    return json.dumps({"keyboards": [{"name": name} for name in names]})


def test_classifies_bluetooth_keyboard_from_udev_bus(tmp_path):
    name = "Keychron K2 [ABC]"
    _write_event(tmp_path, "event4", name)

    def udev(path):
        assert path == "/dev/input/event4"
        return {"ID_BUS": "bluetooth", "ID_INPUT_KEYBOARD": "1"}

    devices = discover(_hypr(name), tmp_path, udev)

    assert devices == [
        {
            "name": name,
            "event": "/dev/input/event4",
            "category": "bluetooth",
            "enabled": None,
            "reason": "udev bus is bluetooth",
        }
    ]


def test_classifies_internal_keyboard_only_with_strong_platform_evidence(tmp_path):
    name = "AT Translated Set 2 keyboard"
    _write_event(tmp_path, "event3", name)

    devices = discover(
        _hypr(name),
        tmp_path,
        lambda path: {
            "ID_BUS": "isa",
            "ID_PATH": "platform-i8042-serio-0",
            "ID_INPUT_KEYBOARD": "1",
        },
    )

    assert devices[0]["category"] == "internal"
    assert "platform" in devices[0]["reason"]


def test_ambiguous_keyboard_is_not_assigned_to_a_toggle_group(tmp_path):
    name = "Mystery keyboard"
    _write_event(tmp_path, "event7", name)

    devices = discover(_hypr(name), tmp_path, lambda path: {})

    assert devices[0]["category"] == "unclassified"
    assert devices[0]["enabled"] is None


def test_exact_name_matching_prefers_keyboard_event_and_excludes_non_keyboard(tmp_path):
    name = "Shared device"
    _write_event(tmp_path, "event1", name)
    _write_event(tmp_path, "event2", name)
    metadata = {
        "/dev/input/event1": {"ID_INPUT_KEYBOARD": "0"},
        "/dev/input/event2": {"ID_INPUT_KEYBOARD": "1", "ID_BUS": "bluetooth"},
    }

    devices = discover(_hypr(name), tmp_path, metadata.__getitem__)

    assert devices[0]["event"] == "/dev/input/event2"
    assert devices[0]["category"] == "bluetooth"


def test_group_state_distinguishes_empty_mixed_and_uniform_groups():
    devices = [
        {"category": "internal", "enabled": True},
        {"category": "bluetooth", "enabled": True},
        {"category": "bluetooth", "enabled": False},
        {"category": "unclassified", "enabled": None},
    ]

    assert group_state(devices, "internal") == "on"
    assert group_state(devices, "bluetooth") == "mixed"
    assert group_state(devices, "unclassified") == "unknown"
