# Security

Keyboard Switcher is an Omarchy shell plugin. Omarchy plugins run unsandboxed
with the user's permissions inside the long-lived `omarchy-shell` process.
Install it only from a source repository you trust and review updates before
enabling them.

## Commands and permissions

The runtime helper invokes only these fixed paths:

- `/usr/bin/python3` to run the bundled standard-library helper.
- `/usr/bin/hyprctl -j devices` to discover current keyboards.
- `/usr/bin/hyprctl -j getoption device[NAME]:enabled` to read state.
- `/usr/bin/hyprctl keyword device[NAME]:enabled true|false` to change state.
- `/usr/bin/udevadm info --query=property --name /dev/input/eventN` to classify
  a keyboard's transport.

It does not use `sudo`, `pkexec`, a daemon, network access, `sh -c`, or shell
interpolation of device names. Device names are passed as individual argv
items, output is bounded, and every mutation follows a fresh discovery pass.

## Safety boundary

Only devices confidently classified as internal or Bluetooth keyboards can be
changed. Touchpads, mice, and unclassified devices are excluded. If metadata
is missing or contradictory, the helper reports the device as unclassified and
does nothing to it.

The plugin changes Hyprland's session-level device handling only. It does not
write `/etc`, udev rules, firmware, Bluetooth pairing data, or persistent input
state. A new login or reboot starts with the normal configuration again.

## Reporting

For a suspected security problem, do not attach private device names or logs.
Open a private report with the repository maintainer and include the plugin
version, Omarchy version, and a minimal reproduction.

