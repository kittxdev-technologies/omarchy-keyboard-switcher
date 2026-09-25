import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import qs.Commons
import qs.Ui
import "Model.js" as Model

Panel {
  id: root
  moduleName: "io.github.dev.keyboard-switcher"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null

  readonly property color foreground: bar ? bar.foreground : Color.foreground
  readonly property color dim: Qt.darker(foreground, 1.55)
  readonly property color accent: Color.accent
  readonly property color panelBorder: Qt.alpha(foreground, 0.16)

  DeviceService { id: service }

  function open() {
    root.controller.show()
    service.refresh()
  }

  function close() { root.controller.hide() }

  function toggle() {
    if (root.opened) root.close()
    else root.open()
  }

  function closeForPopoutSwitch() {
    if (root.opened) root.close()
  }

  function switchPanel(direction) {
    if (root.bar && typeof root.bar.switchPanelFrom === "function")
      return root.bar.switchPanelFrom(root.hostWidget || root, direction)
    return false
  }

  function stateColor(state) {
    if (state === "on") return accent
    if (state === "mixed") return Color.urgent
    return Qt.alpha(foreground, 0.35)
  }

  function toggleTarget(state) { return state !== "on" }

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root.hostWidget || root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(360))
    contentHeight: panel.fittedContentHeight(content.implicitHeight)

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }
      onTextKey: function(text) {
        if (text === "r" || text === "R") service.refresh()
        else if (text === "s" || text === "S") service.restoreDefaults()
      }

      Column {
        id: content
        width: parent.width
        spacing: Style.space(10)

        Text {
          width: parent.width
          text: "Keyboard Switcher"
          color: root.foreground
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.subtitle
          font.bold: true
        }

        Text {
          width: parent.width
          text: "Use the trackpad to choose which keyboards can send input."
          color: root.dim
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.bodySmall
          wrapMode: Text.WordWrap
        }

        Rectangle {
          width: parent.width
          height: 1
          color: root.panelBorder
        }

        Item {
          width: parent.width
          height: 52

          MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: service.setGroup("internal", root.toggleTarget(service.internalState))
          }

          Column {
            anchors.left: parent.left
            anchors.leftMargin: Style.space(4)
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Text {
              text: "Built-in keyboard"
              color: root.foreground
              font.family: root.bar ? root.bar.fontFamily : Style.font.family
              font.pixelSize: Style.font.body
            }
            Text {
              text: Model.stateText(service.internalState, "Not detected")
              color: root.dim
              font.family: root.bar ? root.bar.fontFamily : Style.font.family
              font.pixelSize: Style.font.bodySmall
            }
          }
          SwitchVisual {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            stateName: service.internalState
            tint: root.stateColor(service.internalState)
          }
        }

        Item {
          width: parent.width
          height: 52

          MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: service.setGroup("bluetooth", root.toggleTarget(service.bluetoothState))
          }

          Column {
            anchors.left: parent.left
            anchors.leftMargin: Style.space(4)
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Text {
              text: "Bluetooth keyboards"
              color: root.foreground
              font.family: root.bar ? root.bar.fontFamily : Style.font.family
              font.pixelSize: Style.font.body
            }
            Text {
              text: Model.stateText(service.bluetoothState, "None connected")
              color: root.dim
              font.family: root.bar ? root.bar.fontFamily : Style.font.family
              font.pixelSize: Style.font.bodySmall
            }
          }
          SwitchVisual {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            stateName: service.bluetoothState
            tint: root.stateColor(service.bluetoothState)
          }
        }

        Rectangle {
          width: parent.width
          height: 1
          color: root.panelBorder
        }

        Text {
          width: parent.width
          text: "Detected keyboards"
          color: root.dim
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.bodySmall
          font.bold: true
        }

        Column {
          width: parent.width
          spacing: 4
          Repeater {
            model: service.devices
            delegate: RowLayout {
              width: parent.width
              spacing: Style.space(6)
              Text {
                Layout.fillWidth: true
                text: String(modelData.name || "Unnamed keyboard")
                color: root.foreground
                elide: Text.ElideRight
                font.family: root.bar ? root.bar.fontFamily : Style.font.family
                font.pixelSize: Style.font.bodySmall
              }
              Text {
                text: Model.categoryText(String(modelData.category || ""))
                color: root.dim
                font.family: root.bar ? root.bar.fontFamily : Style.font.family
                font.pixelSize: Style.font.bodySmall
              }
              Text {
                text: modelData.enabled === true ? "ON"
                  : modelData.enabled === false ? "OFF" : "?"
                color: modelData.enabled === true ? root.accent : root.dim
                font.family: root.bar ? root.bar.fontFamily : Style.font.family
                font.pixelSize: Style.font.bodySmall
                font.bold: true
              }
            }
          }
        }

        Text {
          visible: service.devices.length === 0 && service.errorText === ""
          width: parent.width
          text: "No keyboard devices detected yet."
          color: root.dim
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.bodySmall
        }

        Text {
          visible: service.errorText !== ""
          width: parent.width
          text: service.errorText
          color: Color.urgent
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.bodySmall
          wrapMode: Text.WordWrap
        }

        Text {
          visible: service.actionText !== ""
          width: parent.width
          text: service.actionText
          color: root.dim
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.bodySmall
        }

        Rectangle {
          width: parent.width
          height: 34
          radius: 5
          color: resetArea.containsMouse ? Qt.alpha(root.accent, 0.14) : "transparent"
          border.width: 1
          border.color: root.panelBorder

          Text {
            anchors.centerIn: parent
            text: "Restore safe defaults"
            color: root.foreground
            font.family: root.bar ? root.bar.fontFamily : Style.font.family
            font.pixelSize: Style.font.bodySmall
          }
          MouseArea {
            id: resetArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: service.restoreDefaults()
          }
        }

        Text {
          width: parent.width
          text: "Trackpad is never changed. Esc and Caps Lock follow your normal layout."
          color: root.dim
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          wrapMode: Text.WordWrap
        }
      }
    }
  }

  component SwitchVisual: Item {
    property string stateName: "empty"
    property color tint: "white"
    width: 42
    height: 24

    Rectangle {
      anchors.fill: parent
      radius: height / 2
      color: stateName === "on" ? Qt.alpha(tint, 0.9)
        : stateName === "mixed" ? Qt.alpha(tint, 0.62)
        : Qt.alpha(root.foreground, 0.18)
      border.width: 1
      border.color: Qt.alpha(root.foreground, 0.3)
    }
    Rectangle {
      width: 18
      height: 18
      radius: 9
      anchors.verticalCenter: parent.verticalCenter
      x: stateName === "on" ? parent.width - width - 3 : 3
      color: stateName === "on" || stateName === "mixed" ? "white" : root.dim
    }
  }
}
