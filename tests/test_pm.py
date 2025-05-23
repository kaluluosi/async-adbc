from async_adbc.plugins.pm import ClearError, UninstallError
from tests.testcase import DeviceTestCase, ARM_APK, PKG_NAME


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
        await self.device.pm.list_packages()

    async def test_list_features(self):
        await self.device.pm.list_features()
