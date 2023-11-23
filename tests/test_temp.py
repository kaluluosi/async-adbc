from tests.testcase import DeviceTestCase


class TestTempPlugin(DeviceTestCase):
    async def test_temp_emulator(self):
        stat = await self.device.temp.stat()  # type: ignore

        self.assertGreaterEqual(stat.cpu, 0)
        self.assertGreaterEqual(stat.gpu, 0)
        self.assertGreaterEqual(stat.npu, 0)
        self.assertGreaterEqual(stat.battery, 0)
