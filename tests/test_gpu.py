from tests.testcase import DeviceTestCase


class TestGPUPlugin(DeviceTestCase):
    async def test_gpu_info(self):
        info = await self.device.gpu.info()

        self.assertTrue(info.manufactor)
        self.assertTrue(info.name)
        self.assertTrue(info.opengl)
