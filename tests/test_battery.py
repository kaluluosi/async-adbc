from tests.testcase import DeviceTestCase


class TestDeviceBattery(DeviceTestCase):
    async def test_batery(self):
        stat = await self.device.battery.stat()

        self.assertGreater(stat.level, 0)
