import os
import re
from typing import Any, Dict, List, Optional

from async_adbc.service.local import ProgressCallback
from async_adbc.plugin import Plugin, register_plugin
from async_adbc.exceptions import InstallError, UninstallError, ClearError


@register_plugin("pm", "pm")
class PMPlugin(Plugin):
    """Package Manager 插件，封装了 pm 命令"""

    INSTALL_RESULT_PATTERN = r"(Success|Failure|Error)\s?(.*)"
    UNINSTALL_RESULT_PATTERN = r"(Success|Failure.*|.*Unknown package:.*)"
    CLEAR_RESULT_PATTERN = r"(Success|Failed)"

    async def list_packages(self) -> List[str]:
        """列出安装的包

        等同于：adb shell pm list packages

        Returns:
            List[str]: 包名列表
        """
        result = await self._device.shell("pm list packages 2>/dev/null")
        result_pattern = r"^package:(.*?)\r?$"

        packages = []
        for line in result.splitlines():
            m = re.match(result_pattern, line)
            if m:
                packages.append(m.group(1))

        return packages

    async def install(
        self,
        path: str,
        args: str = "rd",
        progress_cb: Optional[ProgressCallback] = None,
    ) -> bool:
        """将路径 path 的 APK 文件推送并用 pm install 安装到手机里

        等同于：adb install path

        args 参数说明：
            - t: 以测试版本安装应用
            - l: 单向锁定该应用程序（不能提取 APK，不能手机里卸载，相当于内置 app 了，需要 root 权限）
            - s: 把 APK 安装到 SD 卡上
            - g: 安装的时候允许所有权限（安装完后不用手动授予各种权限弹窗了，直接默认全给了）
            - r: 强制覆盖安装（不卸载原来的应用重复安装会失败，用这个参数可以直接覆盖）
            - d: 无视版本号（允许低版本覆盖高版本）

        Args:
            path: APK 文件路径
            args: 安装参数，默认 rd
            progress_cb: 进度回调函数

        Returns:
            bool: 成功返回 True

        Raises:
            InstallError: 安装失败时抛出
        """
        args = " ".join([f"-{c}" for c in args])

        base_name = os.path.basename(path)
        dst = f"/data/local/tmp/{base_name}"
        await self._device.push(path, dst, progress_cb=progress_cb)

        try:
            res = await self._device.shell(f"pm install {args} {dst}")
            match = re.search(self.INSTALL_RESULT_PATTERN, res)
            if match and match.group(1) == "Success":
                return True
            elif match:
                groups = match.groups()
                raise InstallError(path, groups)
            else:
                raise InstallError(path, f"android shell 打印:{res}")
        finally:
            await self._device.shell(f"rm -f {dst}")

    async def uninstall(self, package_name: str) -> bool:
        """卸载应用

        等同于：adb uninstall package_name

        Args:
            package_name: 包名

        Returns:
            bool: 成功返回 True

        Raises:
            UninstallError: 卸载失败时抛出
        """
        result = await self._device.shell(f"pm uninstall {package_name}")
        match = re.search(self.UNINSTALL_RESULT_PATTERN, result)

        if match and match.group(1) == "Success":
            return True
        elif match:
            msg = match.group(1)
            raise UninstallError(msg)
        else:
            raise UninstallError("卸载后没有返回任何信息")

    async def path(self, package_name: str) -> str:
        """获取应用的 APK 路径

        Args:
            package_name: 包名

        Returns:
            str: APK 路径
        """
        res = await self._device.shell(f"pm path {package_name}")
        if res and "package:" in res:
            return res.split(":")[1]
        else:
            raise NameError(package_name, "不存在，可能没有安装")

    async def is_installed(self, package_name: str) -> bool:
        """判断应用是否已安装

        Args:
            package_name: 包名

        Returns:
            bool: 已安装返回 True，否则返回 False
        """
        try:
            await self.path(package_name)
            return True
        except NameError:
            return False

    async def clear(self, package_name: str):
        """清除应用的数据和缓存

        等同于：adb shell pm clear package_name

        Args:
            package_name: 包名

        Raises:
            ClearError: 清除失败时抛出
        """
        res = await self._device.shell(f"pm clear {package_name}")

        match = re.search(self.CLEAR_RESULT_PATTERN, res)

        if match is not None and match.group(1) == "Success":
            return
        else:
            raise ClearError(package_name, res.strip())

    async def list_features(self) -> Dict[str, Any]:
        """列出 Android 功能列表

        等同于：adb shell pm list features

        Returns:
            Dict[str, Any]: 功能字典
        """
        result = await self._device.shell("pm list features 2>/dev/null")

        result_pattern = r"^feature:(.*?)(?:=(.*?))?\r?$"
        features = {}
        for line in result.splitlines():
            m = re.match(result_pattern, line)
            if m:
                value = True if m.group(2) is None else m.group(2)
                features[m.group(1)] = value

        return features
