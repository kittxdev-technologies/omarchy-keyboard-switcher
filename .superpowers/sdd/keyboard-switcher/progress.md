# SDD ledger — plan: docs/superpowers/plans/2026-09-25-keyboard-switcher.md

Task 1: complete — scaffold test passes (1 passed)

Task 2: complete — discovery/classification suite passes (6 passed)

Task 3: complete — helper mutation and CLI suite passes (11 passed)

Task 4: complete — QML/manifest tests pass (15 passed), manifest validation exits 0, and qmllint exits 0 with unresolved external Omarchy-module warnings only

Task 5: complete — install transformation tests pass (17 total); live files backed up and updated, but shell rescan/enable could not run because `omarchy-shell` is not running in this session

Task 6: complete — full suite passes (18 passed), manifest validation exits 0, installed copy validates, Python compilation exits 0, qmllint exits 0 with external-module warnings, and git diff check exits 0

Ruling: Task 1's initial layout test checked later-task files and could never turn green at the scaffold stage; narrowed it to scaffold-owned files and kept full publish-layout coverage for Task 4 — this costs no coverage and restores independent task completion.

Final: fixed validator-safe test environment — test_publication_files_and_commands_are_documented RED→GREEN, suite 18/18; documented an external UV_PROJECT_ENVIRONMENT because Omarchy rejects the symlinks created by an in-plugin .venv.

Final review: self-review (no subagent tool); one workflow finding fixed above, no remaining Critical or Important findings.

Final: fixed live Hyprland device mapping — test_matches_hypr_normalized_name_to_sysfs_device_name RED→GREEN, suite 19/19; normalized Hyprland names conservatively before sysfs matching.

Final: fixed live device safety/state handling — test_generic_platform_device_is_not_classified_as_internal and test_list_treats_missing_hyprland_option_as_enabled RED→GREEN, suite 21/21; generic platform controls remain unclassified and unset Hyprland options are treated as enabled.

Final: fixed external widget load — test_bar_widget_imports_ipc_handler_module RED→GREEN, suite 22/22; imported Quickshell.Io for the bar widget's IpcHandler and restarted the Omarchy shell to clear the failed component cache.
