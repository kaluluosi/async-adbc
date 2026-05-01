# ============ service/host.py 异常 ============
class DeviceNotFoundError(Exception):
    def __init__(self, serialno: str, *args: object) -> None:
        super().__init__(f"{serialno} 不存在", *args)


# ============ plugins/pm.py 异常 ============
class InstallError(Exception):
    def __init__(self, src: str, msg) -> None:
        super().__init__(f"{src} 安装失败 - [{msg}]")


class UninstallError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("卸载异常", *args)


class ClearError(Exception):
    def __init__(self, package_name: str, msg) -> None:
        super().__init__(f"{package_name}无法被清除 - [{msg}]")


# ============ plugins/fps.py 异常 ============
class SurfaceNotFoundError(Exception):
    pass


# 兼容旧的导入方式
__all__ = [
    "DeviceNotFoundError",
    "InstallError",
    "UninstallError",
    "ClearError",
    "SurfaceNotFoundError",
]
