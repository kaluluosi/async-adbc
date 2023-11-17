import asyncio
from tests.testcase import DeviceTestCase, PKG_NAME,ARM_APK,UNITY_APK,UNITY_PKG_NAME


class TestFpsPlugin(DeviceTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        await self.device.pm.install(ARM_APK)
        await self.device.pm.install(UNITY_APK)

    async def asyncTearDown(self):
        await super().asyncTearDown()
        await self.device.pm.uninstall(PKG_NAME)
        await self.device.pm.uninstall(UNITY_PKG_NAME)

    async def test_fps_not_game(self):
        await self.device.am.start_app(PKG_NAME)
        await asyncio.sleep(1)
        stat = await self.device.fps.stat(PKG_NAME)
        self.assertEqual(stat.fps,0)

    async def test_fps(self):
        await self.device.am.start_app(UNITY_PKG_NAME)
        await asyncio.sleep(5)
        stat = await self.device.fps.stat(UNITY_PKG_NAME)
        self.assertGreaterEqual(stat.fps,0)

