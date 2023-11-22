from async_adbc.plugin import Plugin
from typing import NamedTuple


class Source(NamedTuple):
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    JOYSTICK = "joystick"
    TOUCHNAVIGATION = "touchnavigation"
    TOUCHPAD = "touchpad"
    TRACKBALL = "trackball"
    DPAD = "dpad"
    STYLUS = "stylus"
    GAMEPAD = "gamepad"
    touchscreen = "touchscreen"


class Input(Plugin):
    # TODO: 按键模拟输入这部分还没有实现
    raise NotImplementedError("未实现")
