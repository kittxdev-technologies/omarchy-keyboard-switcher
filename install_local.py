#!/usr/bin/python3
"""Safely install the development checkout into an Omarchy user config."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


PLUGIN_ID = "io.github.kittxdev-technologies.keyboard-switcher"
PLUGIN_FILES = (
    "manifest.json",
    "BarWidget.qml",
    "Panel.qml",
    "DeviceService.qml",
    "Model.js",
    "keyboard_devices.py",
    "keyboard-devices",
)


def remove_active_xkb_override(source: str) -> str:
    return re.sub(r"^\s*kb_file\s*=.*(?:\n|$)", "", source, flags=re.MULTILINE)


def add_bar_widget(source: str, plugin_id: str = PLUGIN_ID) -> str:
    data = json.loads(source)
    layout = data.setdefault("bar", {}).setdefault("layout", {})
    for section in ("left", "center", "right"):
        entries = layout.setdefault(section, [])
        layout[section] = [entry for entry in entries if entry.get("id") != plugin_id]

    right = layout["right"]
    entry = {"id": plugin_id}
    bluetooth_index = next(
        (index for index, item in enumerate(right) if item.get("id") == "omarchy.bluetooth"),
        len(right),
    )
    right.insert(bluetooth_index, entry)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _backup(path: Path) -> Path:
    backup = path.with_name(path.name + f".bak.keyboard-switcher.{int(time.time())}")
    shutil.copy2(path, backup)
    return backup


def _atomic_write(path: Path, content: str) -> None:
    temporary = path.with_name(path.name + ".keyboard-switcher.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def install(source_dir: Path, config_root: Path) -> list[Path]:
    plugin_dir = config_root / "omarchy" / "plugins" / PLUGIN_ID
    plugin_dir.mkdir(parents=True, exist_ok=True)
    for filename in PLUGIN_FILES:
        source = source_dir / filename
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, plugin_dir / filename)

    hypr_input = config_root / "hypr" / "input.lua"
    shell_config = config_root / "omarchy" / "shell.json"
    changed: list[Path] = []
    if hypr_input.is_file():
        original = hypr_input.read_text(encoding="utf-8")
        updated = remove_active_xkb_override(original)
        if updated != original:
            _backup(hypr_input)
            _atomic_write(hypr_input, updated)
            changed.append(hypr_input)
    if shell_config.is_file():
        original = shell_config.read_text(encoding="utf-8")
        updated = add_bar_widget(original)
        if updated != original:
            _backup(shell_config)
            _atomic_write(shell_config, updated)
            changed.append(shell_config)
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--config-root", type=Path, default=Path.home() / ".config")
    args = parser.parse_args(argv)
    changed = install(args.source, args.config_root)
    print("Installed", PLUGIN_ID)
    for path in changed:
        print("Updated", path)
    print("Next: omarchy plugin validate", args.config_root / "omarchy" / "plugins" / PLUGIN_ID)
    print("Next: omarchy-shell shell rescanPlugins")
    return 0


if __name__ == "__main__":
    sys.exit(main())
