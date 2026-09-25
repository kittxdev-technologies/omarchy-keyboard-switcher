.pragma library

function devicesFor(devices, category) {
  var result = []
  var list = devices || []
  for (var i = 0; i < list.length; i++) {
    if (String(list[i].category || "") === category) result.push(list[i])
  }
  return result
}

function stateFor(devices, category) {
  var rows = devicesFor(devices, category)
  if (rows.length === 0) return "empty"
  var unknown = false
  var on = 0
  for (var i = 0; i < rows.length; i++) {
    if (rows[i].enabled === null || rows[i].enabled === undefined) unknown = true
    else if (rows[i].enabled === true) on++
  }
  if (unknown) return "unknown"
  if (on === rows.length) return "on"
  if (on === 0) return "off"
  return "mixed"
}

function stateText(state, emptyText) {
  if (state === "on") return "Enabled"
  if (state === "off") return "Disabled"
  if (state === "mixed") return "Mixed"
  if (state === "unknown") return "Unavailable"
  return emptyText
}

function categoryText(category) {
  if (category === "internal") return "Built-in"
  if (category === "bluetooth") return "Bluetooth"
  return "Unclassified"
}
