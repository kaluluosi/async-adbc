from async_adbc.plugin import Plugin
from typing import Optional


class ActivityManagerPlugin(Plugin):
    async def start_app(self, package_name: str, activity: Optional[str] = None):
        """
        这个方法应该能够支持直接打开应用的某个Activity

        Args:
            package_name (str): 包名
            active_name (str, optional): 目标Activity. Defaults to "MainActivity".
        """
        if not activity:
            await self._device.shell(
                f"monkey -p {package_name} -c 'android.intent.category.LAUNCHER' 1"
            )
        else:
            await self._device.shell(
                f"am start {package_name}/{package_name}.{activity}"
            )
            result = await self._device.shell(
                f'dumpsys SurfaceFlinger --list|grep "{package_name}"'
            )
            if package_name not in result:
                # XXX: 保底再用monkey方案拉起
                await self._device.shell(
                    f"monkey -p {package_name} -c 'android.intent.category.LAUNCHER' 1"
                )

    async def stop_app(self, package_name: str):
        """
        关闭应用

        Args:
            package_name (str): 包名
        """
        await self._device.shell(f"am force-stop {package_name}")
