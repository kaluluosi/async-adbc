
from tests.testcase import DeviceTestCase


class TestMinicapPlugin(DeviceTestCase):
    async def test_init(self):
        data = await self.device.minicap.get_frame()
        self.assertTrue(data)
