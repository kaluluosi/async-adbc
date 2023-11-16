from tests.testcase import DeviceTestCase,ARM_APK,PKG_NAME

class TestDeviceAMPlugin(DeviceTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        await self.device.pm.install(ARM_APK)

    async def asyncTearDown(self):
        await super().asyncTearDown()
        await self.device.pm.uninstall(PKG_NAME)

    async def test_startapp(self):
        await self.device.am.start_app(PKG_NAME)

        result = await self.device.shell(
            f'dumpsys SurfaceFlinger --list|grep "{PKG_NAME}"'
        )
        self.assertTrue(PKG_NAME in result)

    async def test_stopapp(self):
        await self.device.am.start_app(PKG_NAME)
        await self.device.am.stop_app(PKG_NAME)