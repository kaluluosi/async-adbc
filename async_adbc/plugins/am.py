from . import Plugin


class ActivityManagerPlugin(Plugin):
    async def start_app(self, package_name: str):
        """这个方法应该能够支持直接打开应用的某个Activity

        Args:
            package_name (str): 包名
            active_name (str, optional): 目标Activity. Defaults to "MainActivity".
        """
        await self._device.shell(f"am start {package_name}")
