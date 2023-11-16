from typing import Optional
from async_adbc.plugin import Plugin


class UtilsPlugin(Plugin):
    """
    工具函数插件，一些不好分类的工具函数都仍这里

    """

    async def screencap(self, save_file: Optional[str] = None) -> bytes:
        """原生截屏，效率很慢，建议用minicap代替

        Args:
            save_file (str | None, optional): 保存文件，png格式，为空就不保存. Defaults to None.

        Returns:
            bytes: 返回二进制数据
        """
        result = await self._device.shell_raw("/system/bin/screencap -p")
        if result and len(result) > 5 and result[5] == 0x0D:
            result = result.replace(b"\r\n", b"\n")

        if save_file:
            with open(save_file, "wb") as f:
                f.write(result)

        return result
