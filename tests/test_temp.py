from tests.testcase import DeviceTestCase


class TestTempPlugin(DeviceTestCase):
    async def test_temp(self):
        stat = await self.device.temp.stat()

        self.assertGreater(stat.cpu, 0)
        self.assertGreater(stat.gpu, 0)
        self.assertGreater(stat.npu, 0)
        self.assertGreater(stat.battery, 0)
