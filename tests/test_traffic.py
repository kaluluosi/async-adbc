import asyncio
from tests.testcase import DeviceTestCase


class TestTrafficPlugin(DeviceTestCase):
    async def test_traffic(self):
        chrome_pkg_name = "com.android.chrome"
        # chrome_pkg_name = "com.huawei.browser"
        await self.device.am.stop_app(chrome_pkg_name)
        await self.device.am.start_app(chrome_pkg_name)
        await asyncio.sleep(2)
        stat = await self.device.traffic.stat()
        await asyncio.sleep(2)
        stat = await self.device.traffic.stat()

        self.assertGreater(stat.receive, 0)

        # await asyncio.sleep(2)
        # stat = await self.device.traffic.stat(chrome_pkg_name)
        # await asyncio.sleep(2)
        # stat = await self.device.traffic.stat(chrome_pkg_name)

        # self.assertGreater(stat.receive, 0)
