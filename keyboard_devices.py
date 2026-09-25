#!/usr/bin/env python3
"""Safe, dependency-free keyboard discovery primitives for the bar plugin."""

from __future__ import annotations

import json
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence


UdevReader = Callable[[str], Mapping[str, str]]
CommandRunner = Callable[..., object]
HYPRCTL = "/usr/bin/hyprctl"
UDEVADM = "/usr/bin/udevadm"
SYSFS_ROOT = Path("/sys")


class CommandError(RuntimeError):
    pass


def _execute(
    executable: str,
    args: Sequence[str],
    command_runner: CommandRunner = subprocess.run,
) -> str:
    result = command_runner(
        [executable, *args],
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )
    if getattr(result, "returncode", 1) != 0:
        error = str(getattr(result, "stderr", "") or "command failed").strip()
        raise CommandError(error[:240])
    output = str(getattr(result, "stdout", ""))
    if len(output) > 1_000_000:
        raise CommandError("command output exceeded limit")
    return output


def _udev_reader(udevadm_path: str, command_runner: CommandRunner) -> UdevReader:
    def read(event: str) -> Mapping[str, str]:
        output = _execute(
            udevadm_path,
            ["info", "--query=property", "--name", event],
            command_runner,
        )
        properties: dict[str, str] = {}
        for line in output.splitlines():
            key, separator, value = line.partition("=")
            if separator and key and "\x00" not in line:
                properties[key] = value
        return properties

    return read


def _live_devices(
    hyprctl_path: str,
    udevadm_path: str,
    sysfs_root: Path,
    command_runner: CommandRunner,
) -> list[dict]:
    hypr_json = _execute(hyprctl_path, ["-j", "devices"], command_runner)
    devices = discover(
        hypr_json,
        sysfs_root,
        _udev_reader(udevadm_path, command_runner),
    )
    for device in devices:
        if not device["event"]:
            continue
        option = f"device[{device['name']}]:enabled"
        try:
            option_json = _execute(
                hyprctl_path,
                ["-j", "getoption", option],
                command_runner,
            )
            if option_json.strip().lower() == "no such option":
                device["enabled"] = True
            else:
                device["enabled"] = parse_enabled_value(json.loads(option_json))
        except (CommandError, json.JSONDecodeError):
            device["enabled"] = None
    return devices


def _json_output(payload: Mapping[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def build_device_eval_args(name: str, enabled: bool) -> list[str]:
    """Build one argv-safe Hyprland Lua device toggle command."""

    if not name:
        raise ValueError("device name must not be empty")
    lua_name = json.dumps(name, ensure_ascii=False)
    lua_enabled = "true" if enabled else "false"
    return ["eval", f"hl.device({{ name = {lua_name}, enabled = {lua_enabled} }})"]


def apply_group(
    devices: list[Mapping[str, object]],
    group: str,
    enabled: bool,
    runner: Callable[[list[str]], object],
) -> dict:
    """Apply a group toggle only to confidently classified keyboards."""

    if group not in {"internal", "bluetooth", "all"}:
        raise ValueError("unsupported keyboard group")

    categories = {"internal", "bluetooth"} if group == "all" else {group}
    changed: list[str] = []
    failed: list[str] = []
    for device in devices:
        name = str(device.get("name", ""))
        if device.get("category") not in categories or not name:
            continue
        try:
            runner(build_device_eval_args(name, enabled))
        except Exception:
            failed.append(name)
        else:
            changed.append(name)

    return {"ok": not failed, "changed": changed, "failed": failed}


def parse_enabled_value(value: Mapping[str, object]) -> bool | None:
    """Parse `hyprctl getoption -j` while treating an unset option as enabled."""

    if value.get("set") is False:
        return True
    if isinstance(value.get("int"), int) and value["int"] in (0, 1):
        return bool(value["int"])
    raw = value.get("str")
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def _event_candidates(sysfs_root: Path, name: str) -> list[str]:
    normalized_name = _normalized_device_name(name)
    candidates: list[str] = []
    for name_file in sorted(sysfs_root.glob("class/input/event*/device/name")):
        try:
            sysfs_name = name_file.read_text(encoding="utf-8").strip()
            if _normalized_device_name(sysfs_name) == normalized_name:
                candidates.append("/dev/input/" + name_file.parts[-3])
        except OSError:
            continue
    return candidates


def _normalized_device_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")


def _metadata(reader: UdevReader, event: str) -> Mapping[str, str]:
    try:
        return dict(reader(event))
    except (OSError, KeyError, ValueError):
        return {}


def _classification(metadata: Mapping[str, str]) -> tuple[str, str]:
    bus = str(metadata.get("ID_BUS", "")).lower()
    path = str(metadata.get("ID_PATH", "")).lower()

    if bus == "bluetooth" or "bluetooth" in path:
        return "bluetooth", "udev bus is bluetooth"

    internal_buses = {"isa", "i2c", "serio", "acpi"}
    if bus in internal_buses:
        return "internal", f"udev bus is {bus}; internal platform device"
    if any(token in path for token in ("i8042", "serio")):
        return "internal", "udev path contains platform/serio"

    return "unclassified", "udev metadata is not definitive"


def discover(
    hypr_json: str,
    sysfs_root: Path,
    udev_reader: UdevReader,
) -> list[dict]:
    """Return one safe record for each keyboard Hyprland currently reports."""

    payload = json.loads(hypr_json)
    records: list[dict] = []
    for item in payload.get("keyboards", []):
        name = str(item.get("name", ""))
        if not name:
            continue

        candidates = _event_candidates(sysfs_root, name)
        scored: list[tuple[int, str, Mapping[str, str]]] = []
        for event in candidates:
            metadata = _metadata(udev_reader, event)
            if metadata.get("ID_INPUT_KEYBOARD") == "0":
                continue
            score = 1 if metadata.get("ID_INPUT_KEYBOARD") == "1" else 0
            category, _ = _classification(metadata)
            if category in {"internal", "bluetooth"}:
                score += 1
            scored.append((score, event, metadata))

        event = ""
        metadata: Mapping[str, str] = {}
        if scored:
            _, event, metadata = max(scored, key=lambda row: (row[0], row[1]))

        category, reason = _classification(metadata)
        records.append(
            {
                "name": name,
                "event": event,
                "category": category,
                "enabled": None,
                "reason": reason,
            }
        )

    return records


def group_state(devices: list[Mapping[str, object]], category: str) -> str:
    states = [device.get("enabled") for device in devices if device.get("category") == category]
    if not states:
        return "empty"
    if any(state is None for state in states):
        return "unknown"
    if all(state is True for state in states):
        return "on"
    if all(state is False for state in states):
        return "off"
    return "mixed"


def main(
    argv: Sequence[str] | None = None,
    *,
    hyprctl_path: str = HYPRCTL,
    udevadm_path: str = UDEVADM,
    sysfs_root: Path = SYSFS_ROOT,
    command_runner: CommandRunner = subprocess.run,
) -> int:
    parser = argparse.ArgumentParser(prog="keyboard-devices")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list")
    set_parser = subparsers.add_parser("set-group")
    set_parser.add_argument("--group", choices=("internal", "bluetooth", "all"), required=True)
    set_parser.add_argument("--enabled", choices=("true", "false"), required=True)
    args = parser.parse_args(argv)

    try:
        devices = _live_devices(
            hyprctl_path,
            udevadm_path,
            Path(sysfs_root),
            command_runner,
        )
        if args.command == "list":
            _json_output({"ok": True, "devices": devices})
            return 0

        desired = args.enabled == "true"

        def runner(command_args: list[str]) -> None:
            output = _execute(hyprctl_path, command_args, command_runner)
            if output.strip().lower() != "ok":
                raise CommandError(output.strip() or "Hyprland rejected device update")

        result = apply_group(devices, args.group, desired, runner)
        _json_output(result)
        return 0 if result["ok"] else 1
    except (CommandError, OSError, ValueError, json.JSONDecodeError) as error:
        _json_output({"ok": False, "devices": [], "error": str(error)[:240]})
        return 1


if __name__ == "__main__":
    sys.exit(main())
