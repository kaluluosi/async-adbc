from typing import Literal, Optional, Union
from async_adbc.plugin import Plugin

"""
Usage: input [<source>] [-d DISPLAY_ID] <command> [<arg>...]

The sources are:
      dpad
      keyboard
      mouse
      touchpad
      gamepad
      touchnavigation
      joystick
      touchscreen
      stylus
      trackball

-d: specify the display ID.
      (Default: -1 for key event, 0 for motion event if not specified.)
The commands and default sources are:
      text <string> (Default: touchscreen)
      keyevent [--longpress] <key code number or name> ... (Default: keyboard)
      tap <x> <y> (Default: touchscreen)
      swipe <x1> <y1> <x2> <y2> [duration(ms)] (Default: touchscreen)
      draganddrop <x1> <y1> <x2> <y2> [duration(ms)] (Default: touchscreen)
      press (Default: trackball)
      roll <dx> <dy> (Default: trackball)
      event <DOWN|UP|MOVE> <x> <y> (Default: touchscreen)

"""


class InputPlugin(Plugin):
    # TODO: 按键模拟输入这部分还没有实现

    async def text(self, text: str):
        await self._device.shell(f"input text {text}")

    async def keyevent(self, key: Union[int, str], long_press: bool = False):
        """
        按键事件

        NOTE:按键码和按键名参考 https://developer.android.com/reference/android/view/KeyEvent

        Args:
            key (Union[int, str]): 按键码或者按键名。
            long_press (bool, optional): 长按. Defaults to False.
        """
        await self._device.shell(
            f"input keyevent {key} {'--longpress' if long_press else ''}"
        )

    async def tap(self, x: int, y: int):
        await self._device.shell(f"input tap {x} {y}")

    async def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration: Optional[int] = None,
    ):
        await self._device.shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")

    async def drag_and_drop(
        self, x1: int, y1: int, x2: int, y2: int, duration: Optional[int] = None
    ):
        await self._device.shell(
            f"input draganddrop {x1} {y1} {x2} {y2} {duration if duration else ''}"
        )

    async def press(self):
        """
        轨迹球点击

        NOTE: 跟`tap`不同的地方是，`press`要搭配`roll`使用。通过`roll`将鼠标移动到某个坐标，然后`press`按下轨迹球点击，那么就会在鼠标坐标下面点击。
        """
        await self._device.shell("input press")

    async def roll(self, x: int, y: int):
        """
        移动轨迹球

        Args:
            x (int): X偏移
            y (int): Y偏移
        """
        await self._device.shell(f"input roll {x} {y}")

    async def event(self, event_type: Literal["DOWN", "UP", "MOVE"], x: int, y: int):
        """
        原始的移动按下弹起触摸事件。

        NOTE: 这是很原始的通过事件来驱动的方法，`tap`等高级方法底层上也是通过这个方法实现。
        这个方法公开的目的是方便用户去自己实现一些复杂的操作，比如签名、画图、组合手势。


        Args:
            event_type (Literal[&quot;DOWN&quot;,&quot;UP&quot;,&quot;MOVE&quot;]): 类型
            x (int): X坐标
            y (int): Y坐标
        """

        await self._device.shell(f"input event {event_type} {x} {y}")
