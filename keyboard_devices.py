#!/usr/bin/env python3
"""Safe, dependency-free keyboard discovery primitives for the bar plugin."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Mapping


UdevReader = Callable[[str], Mapping[str, str]]


def _event_candidates(sysfs_root: Path, name: str) -> list[str]:
    candidates: list[str] = []
    for name_file in sorted(sysfs_root.glob("class/input/event*/device/name")):
        try:
            if name_file.read_text(encoding="utf-8").strip() == name:
                candidates.append("/dev/input/" + name_file.parts[-3])
        except OSError:
            continue
    return candidates


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

    internal_buses = {"isa", "platform", "i2c", "serio", "acpi"}
    if bus in internal_buses:
        return "internal", f"udev bus is {bus}; internal platform device"
    if any(token in path for token in ("platform", "i8042", "serio")):
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
