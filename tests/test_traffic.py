import asyncio
import unittest
from tests.testcase import DeviceTestCase,IS_DOCKER_ANDROID


class TestTrafficPlugin(DeviceTestCase):
    
    @unittest.skipIf(not IS_DOCKER_ANDROID, "这个用例只运行在docker android容器")
    async def test_traffic(self):
        chrome_pkg_name = "com.android.chrome"
        await self.device.am.stop_app(chrome_pkg_name)
        await self.device.am.start_app(chrome_pkg_name)
        await asyncio.sleep(2)
        stat = await self.device.traffic.stat()
        await asyncio.sleep(2)
        stat = await self.device.traffic.stat()
        
        self.assertGreater(stat.receive,0)