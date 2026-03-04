# The CatanWindow class itself — now slim.
# Only contains __init__, on_draw, on_mouse_motion, on_mouse_press,
# placement logic (_place_settlement, _place_road, _cancel_build, _end_turn),
# and sprite/text loading. All drawing is delegated to hud.py, ports.py, and drawing.py.