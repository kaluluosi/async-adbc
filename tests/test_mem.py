from adbc.plugins.mem import MemStat
from tests.testcase import DeviceTestCase

ARM_APK = r"tests\assets\app-armeabi-v7a.apk"
PKG_NAME = "com.cloudmosa.helloworldapk"


class TestMemPlugin(DeviceTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        await self.device.pm.install(ARM_APK)

    async def asyncTearDown(self):
        await super().asyncTearDown()
        await self.device.pm.uninstall(PKG_NAME)

    async def test_info(self):
        info = await self.device.mem.info
        self.assertTrue(info.mem_total)

    async def test_stat(self):
        await self.device.am.start_app(PKG_NAME)

        stat: MemStat = await self.device.mem.stat(PKG_NAME)
        self.assertGreater(stat.pss, 0)
