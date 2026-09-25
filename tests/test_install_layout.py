import json

from install_local import add_bar_widget, remove_active_xkb_override


def test_remove_active_xkb_override_keeps_other_input_settings():
    source = """hl.config({
  input = {
    kb_layout = \"us\",
    kb_file = \"/home/dev/.config/hypr/no-physical-esc.xkb\",
    repeat_rate = 40,
  },
})
"""

    result = remove_active_xkb_override(source)

    assert "kb_file" not in result
    assert 'kb_layout = "us"' in result
    assert "repeat_rate = 40" in result


def test_add_bar_widget_places_it_once_before_bluetooth():
    source = {
        "version": 1,
        "bar": {
            "layout": {
                "right": [
                    {"id": "omarchy.tray"},
                    {"id": "omarchy.bluetooth"},
                    {"id": "omarchy.clock"},
                ]
            }
        },
    }

    result = add_bar_widget(json.dumps(source), "io.github.dev.keyboard-switcher")
    data = json.loads(result)
    ids = [item["id"] for item in data["bar"]["layout"]["right"]]

    assert ids.count("io.github.dev.keyboard-switcher") == 1
    assert ids.index("io.github.dev.keyboard-switcher") < ids.index("omarchy.bluetooth")

