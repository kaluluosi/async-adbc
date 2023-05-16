from async_adbc.plugins.fps import FpsStat, SurfaceNotFoundError
from tests.testcase import DeviceTestCase

ARM_APK = r"tests\assets\app-armeabi-v7a.apk"
PKG_NAME = "com.cloudmosa.helloworldapk"


class TestFpsPlugin(DeviceTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        await self.device.pm.install(ARM_APK)

    async def asyncTearDown(self):
        await super().asyncTearDown()
        await self.device.pm.uninstall(PKG_NAME)

    async def test_fps(self):
        await self.device.am.start_app(PKG_NAME)
        with self.assertRaises(SurfaceNotFoundError):
            stat = await self.device.fps.stat(PKG_NAME)

    # todo: fps工具只能抓取游戏视频应用SurfaceView的帧率
    # 缺乏测试用游戏APP
