from . import Plugin


class Source:
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
    raise NotImplementedError("未实现")
    pass
