"""
author:        kaluluosi111 <kaluluosi@gmail.com>
date:          2023-11-23 10:17:46
Copyright © Kaluluosi All rights reserved
"""

from tests.testcase import DeviceTestCase


class TestInput(DeviceTestCase):
    async def test_text(self):
        await self.device.input.text("hello")

    async def test_keyevent(self):
        await self.device.input.keyevent("KEYCODE_HOME")
        await self.device.input.keyevent(3)

    async def test_tap(self):
        await self.device.input.tap(200, 200)

    async def test_swipe(self):
        await self.device.input.swipe(200, 200, 300, 300)

    async def test_press(self):
        await self.device.input.press()

    async def test_roll(self):
        await self.device.input.roll(10, 10)

    async def test_drag(self):
        await self.device.input.drag_and_drop(200, 200, 300, 300, 1000)
