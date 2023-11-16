from tests.testcase import DeviceTestCase


class TestDeviceBattery(DeviceTestCase):
    async def test_batery(self):
        await self.device.battery.stat()

