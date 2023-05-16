from async_adbc.plugins.pm import ClearError, UninstallError
from tests.testcase import DeviceTestCase

ARM_APK = r"tests\assets\app-armeabi-v7a.apk"
PKG_NAME = "com.cloudmosa.helloworldapk"


class TestDevicePMPlugin(DeviceTestCase):
    async def test_install_uninstall(self):
        await self.device.pm.install(ARM_APK)

        installed = await self.device.pm.is_installed(PKG_NAME)
        self.assertTrue(installed)

        await self.device.pm.uninstall(PKG_NAME)

        installed = await self.device.pm.is_installed(PKG_NAME)
        self.assertFalse(installed)

    async def test_uninstall_not_exist_pakcage(self):
        with self.assertRaises(UninstallError):
            await self.device.pm.uninstall("com.not_exist.app")

    async def test_clear(self):
        await self.device.pm.clear("com.android.phone")

        with self.assertRaises(ClearError):
            await self.device.pm.clear("com.not_exist.app")

    async def test_list_packages(self):
        packages = await self.device.pm.list_packages()
        self.assertTrue("com.android.phone" in packages)

    async def test_list_features(self):
        result = await self.device.pm.list_features()
        self.assertTrue("reqGlEsVersion" in result)
        self.assertTrue("android.hardware.camera" in result)
