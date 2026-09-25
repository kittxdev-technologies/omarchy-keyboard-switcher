import QtQuick
import Quickshell.Io
import "Model.js" as Model

Item {
  id: root

  property var devices: []
  property var sessionState: ({})
  property bool pendingEnabled: true
  property string errorText: ""
  property string actionText: ""
  readonly property bool busy: listProcess.running || actionProcess.running
  readonly property string internalState: Model.stateFor(devices, "internal")
  readonly property string bluetoothState: Model.stateFor(devices, "bluetooth")

  readonly property string pluginDir: {
    var dir = String(Qt.resolvedUrl("."))
    if (dir.indexOf("file://") === 0) dir = dir.substring(7)
    return dir.replace(/\/$/, "")
  }
  readonly property string helperPath: pluginDir + "/keyboard-devices"

  function refresh() {
    if (listProcess.running || actionProcess.running) return
    errorText = ""
    listProcess.command = [root.helperPath, "list"]
    listProcess.running = true
  }

  function parseList(raw) {
    try {
      var payload = JSON.parse(raw || "")
      if (!payload.ok) {
        errorText = String(payload.error || "Keyboard discovery failed")
        return
      }
      var nextDevices = payload.devices || []
      var seen = ({})
      for (var i = 0; i < nextDevices.length; i++) {
        var name = String(nextDevices[i].name || "")
        seen[name] = true
        if (sessionState[name] !== undefined)
          nextDevices[i].enabled = sessionState[name]
      }
      for (var oldName in sessionState) {
        if (!seen[oldName]) delete sessionState[oldName]
      }
      devices = nextDevices
      errorText = ""
    } catch (error) {
      errorText = "Keyboard helper returned invalid data"
    }
  }

  function rememberChanges(changed) {
    var updated = (devices || []).slice()
    for (var i = 0; i < changed.length; i++) {
      var name = String(changed[i] || "")
      if (!name) continue
      sessionState[name] = pendingEnabled
      for (var j = 0; j < updated.length; j++) {
        if (String(updated[j].name || "") === name)
          updated[j].enabled = pendingEnabled
      }
    }
    devices = updated
  }

  function parseAction(raw) {
    try {
      var payload = JSON.parse(raw || "")
      rememberChanges(payload.changed || [])
      if (!payload.ok) {
        actionText = "Some devices could not be changed"
        errorText = String(payload.error || actionText)
      } else {
        actionText = payload.changed && payload.changed.length > 0
          ? "Keyboard state updated" : "No change needed"
        errorText = ""
      }
    } catch (error) {
      actionText = "Keyboard state could not be confirmed"
      errorText = actionText
    }
    refreshTimer.restart()
  }

  function setGroup(group, enabled) {
    if (actionProcess.running || (group !== "internal" && group !== "bluetooth")) return
    pendingEnabled = enabled
    actionText = enabled ? "Enabling keyboards…" : "Disabling keyboards…"
    actionProcess.command = [root.helperPath, "set-group", "--group", group,
                             "--enabled", enabled ? "true" : "false"]
    actionProcess.running = true
  }

  function restoreDefaults() {
    if (actionProcess.running) return
    pendingEnabled = true
    actionText = "Restoring keyboard defaults…"
    actionProcess.command = [root.helperPath, "set-group", "--group", "all",
                             "--enabled", "true"]
    actionProcess.running = true
  }

  Process {
    id: listProcess
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.parseList(text)
    }
    stderr: StdioCollector { waitForEnd: true }
  }

  Process {
    id: actionProcess
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.parseAction(text)
    }
    stderr: StdioCollector { waitForEnd: true }
  }

  Timer {
    id: refreshTimer
    interval: 250
    repeat: false
    onTriggered: root.refresh()
  }

  Timer {
    interval: 5000
    repeat: true
    running: true
    onTriggered: root.refresh()
  }

  Component.onCompleted: refresh()
}
