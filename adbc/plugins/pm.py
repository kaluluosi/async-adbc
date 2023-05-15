from .plugin import Plugin


class InstallError(Exception):
    def __init__(self, src: str, msg) -> None:
        super().__init__(f"{src} 安装失败 - [{msg}]")


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

    async def list_packages(self) -> list[str]:
        result = await self._device.shell("pm list packages 2>/dev/null")
        result_pattern = r"^package:(.*?)\r?$"

        packages = []
        for line in result.split("\n"):
            m = re.match(result_pattern, line)
            if m:
                packages.append(m.group(1))

        return packages

    def install(self, path: str, args="rd"):
        """
        将路径path的apk文件推送并用pm install安装到手机里

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
        self.device.push(path, dest)

        try:
            result = self.device.shell(f"pm install {args} {dest}")
            match = re.search(self.INSTALL_RESULT_PATTERN, result)
            if match and match.group(1) == "Success":
                return True
            elif match:
                groups = match.groups()
                raise InstallError(path, groups)
            else:
                raise InstallError(path, result)

        finally:
            self.device.shell(f"rm -f {dest}")

    def uninstall(self, package_name: str):
        result = self.device.shell(f"pm uninstall {package_name}")
        match = re.search(self.UNINSTALL_RESULT_PATTERN, result)

        if match and match.group(1) == "Success":
            return True
        elif match:
            logger.error(match.group(1))
            return False
        else:
            logger.error("卸载后没有返回任何信息")
            return False

    def is_installed(self, package_name: str):
        """
        检查某个包名的app是否已经安装

        Args:
            self (_type_): _description_
        """

        result = self.device.shell(f"pm path {package_name}")

        if "package:" in result:
            return True
        else:
            return False

    def clear(self, package_name: str) -> bool:
        """
        清除app的缓存

        Args:
            package_name (str): 包名

        Raises:
            ClearError: 清除失败异常

        Returns:
            bool: 成功返回True
        """

        result = self.device.shell(f"pm clear {package_name}")

        match = re.search(self.CLEAR_RESULT_PATTERN, result)

        if match is not None and match.group(1) == "Success":
            return True
        else:
            logger.error(result)
            raise ClearError(package_name, result.strip())

    def list_features(self) -> dict[str, Any]:
        """
        列出安卓功能列表（features）

        Returns:
            dict[str,str]:
        """
        result = self.device.shell("pm list features 2>/dev/null")

        result_pattern = "^feature:(.*?)(?:=(.*?))?\r?$"
        features = {}
        for line in result.split("\n"):
            m = re.match(result_pattern, line)
            if m:
                value = True if m.group(2) is None else m.group(2)
                features[m.group(1)] = value

        return features
