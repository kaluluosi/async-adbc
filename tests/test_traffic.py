import asyncio
from tests.testcase import DeviceTestCase


class TestTrafficPlugin(DeviceTestCase):
    async def test_traffic(self):
        i = 5
        while i:
            stat = await self.device.traffic.stat()
            await asyncio.sleep(1)
            i -= 1

        self.assertGreater(stat.receive, 0)
