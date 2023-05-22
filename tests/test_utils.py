import os
import tempfile
import time

from tests.testcase import DeviceTestCase


class TestUtilPlugin(DeviceTestCase):
    async def test_screencap(self):
        with tempfile.TemporaryDirectory() as dir:
            pic_path = os.path.join(dir, "screencap.png")
            data = await self.device.utils.screencap(pic_path)
            self.assertTrue(data)
            self.assertTrue(os.path.exists(pic_path))
