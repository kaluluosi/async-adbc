import os
import re
from typing import Any, Dict, List, Optional

from async_adbc.service.local import ProgressCallback
from async_adbc.plugin import Plugin


class InstallError(Exception):
    def __init__(self, src: str, msg) -> None:
        super().__init__(f"{src} 安装失败 - [{msg}]")


class UninstallError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("卸载异常", *args)


class ClearError(Exception):
    def __init__(self, package_name: str, msg) -> None:
        super().__init__(f"{package_name}无法被清除 - [{msg}]")


class PMPlugin(Plugin):
    """
    PackageManager插件
    封装了 pm命令

    """

    INSTALL_RESULT_PATTERN = r"(Success|Failure|Error)\s?(.*)"
    UNINSTALL_RESULT_PATTERN = r"(Success|Failure.*|.*Unknown package:.*)"
    CLEAR_RESULT_PATTERN = r"(Success|Failed)"

    async def list_packages(self) -> List[str]:
        """列出安装的包

        等同于： adb shell pm list packages

        Returns:
            list[str]: 包名列表
        """

        result = await self._device.shell("pm list packages 2>/dev/null")
        result_pattern = r"^package:(.*?)\r?$"

        packages = []
        for line in result.split("\n"):
            m = re.match(result_pattern, line)
            if m:
                packages.append(m.group(1))

        return packages

    async def install(
        self, path: str, args="rd", progesss_cb: Optional[ProgressCallback] = None
    ):
        """
        将路径path的apk文件推送并用pm install安装到手机里

        等同于： adb install

        args参数说明：

        -t 以测试版本安装app，允许测试（应该是android应用测试方案的一环，不是很了解）\n
        -l 单向锁定该应用程序（不能提取apk，不能手机里卸载，相当于内置app了，需要root权限，
        不然无法用这个参数安装）\n
        -s 把apk安装到sd卡上\n
        -g 安装的时候允许所有权限（安装完后不用自己受点各种权限弹窗了，直接默认全给了）\n
        -r 强制覆盖安装（不卸载原来的app重复安装会失败，用这个参数可以直接覆盖）\n
        -d 无视版本号（允许低版本覆盖高版本）\n

        Args:
            path (str): _description_
            args (str, optional): lrtsdg 等同 adb install的参数. Defaults to "rd".
        """

        args = " ".join([f"-{c}" for c in args])

        base_name = os.path.basename(path)
        dest = f"/data/local/tmp/{base_name}"
        await self._device.push(path, dest, progress_cb=progesss_cb)

        try:
            res = await self._device.shell(f"pm install {args} {dest}")
            match = re.search(self.INSTALL_RESULT_PATTERN, res)
            if match and match.group(1) == "Success":
                return True
            elif match:
                groups = match.groups()
                raise InstallError(path, groups)
            else:
                raise InstallError(path, f"android shell 打印:{res}")

        finally:
            await self._device.shell(f"rm -f {dest}")

    async def uninstall(self, package_name: str):
        """卸载app

        等同于：adb uninstall

        Args:
            package_name (str): 包名 com.xxx.xxx

        Raises:
            UninstallError: 卸载异常，失败会返回异常
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
        res = await self._device.shell(f"pm path {package_name}")
        if res and "package:" in res:
            return res.split(":")[1]
        else:
            raise NameError(package_name, "不存在，可能没有安装")

    async def is_installed(self, package_name: str) -> bool:
        try:
            await self.path(package_name)
            return True
        except NameError:
            return False

    async def clear(self, package_name: str):
        """
        清除app的缓存

        等同于： adb shell pm clear

        Args:
            package_name (str): 包名

        Raises:
            ClearError: 清除失败异常

        Returns:
            bool: 成功返回True
        """

        res = await self._device.shell(f"pm clear {package_name}")

        match = re.search(self.CLEAR_RESULT_PATTERN, res)

        if match is not None and match.group(1) == "Success":
            return
        else:
            raise ClearError(package_name, res.strip())

    async def list_features(self) -> Dict[str, Any]:
        """
        列出安卓功能列表（features）

        等同于： adb shell pm list features

        Returns:
            dict[str,str]:
        """
        result = await self._device.shell("pm list features 2>/dev/null")

        result_pattern = "^feature:(.*?)(?:=(.*?))?\r?$"
        features = {}
        for line in result.split("\n"):
            m = re.match(result_pattern, line)
            if m:
                value = True if m.group(2) is None else m.group(2)
                features[m.group(1)] = value

        return features
