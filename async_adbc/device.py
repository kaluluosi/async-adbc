import enum
import re
import typing

from async_lru import alru_cache
from async_adbc.protocol.connection import Connection
from async_adbc.service.local import LocalService

from async_adbc.plugins._registry import get_registry


if typing.TYPE_CHECKING:
    from async_adbc.adbclient import ADBClient


class Status(enum.Enum):
    DEVICE = "device"
    OFFLINE = "offline"
    UNKNOWN = "unknown"
    UNAUTHORIZED = "unauthorized"
    AUTHORIZING = "authorizing"


class Device(LocalService):
    def __init__(self, adbc: "ADBClient", serialno: str) -> None:
        self.adbc = adbc
        self.serialno = serialno

        self._load_plugins()

    def _load_plugins(self):
        registry = get_registry()
        for metadata in registry.get_all():
            plugin = metadata.plugin_class(self)
            setattr(self, metadata.attr_name, plugin)

    async def create_connection(self) -> Connection:
        conn = await self.adbc.create_connection()
        await conn.transport_mode(self.serialno)
        return conn

    @alru_cache
    async def get_properties(self) -> typing.Dict[str, str]:
        """获取设备属性

        Returns:
            dict[str, str]: 设备属性字典
        """
        res = await self.shell("getprop")
        result_pattern = r"^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$"
        lines = res.splitlines()
        properties = {}
        for line in lines:
            m = re.match(result_pattern, line)
            if m:
                properties[m.group(1)] = m.group(2)

        return properties

    async def get_pid_by_pkgname(self, package_name: str) -> int:
        result = await self.shell(f"pidof {package_name}")
        if result:
            return int(result)
        else:
            raise ValueError(f"{package_name} 应用没有运行")

    async def file_exists(self, file_path: str) -> bool:
        """判断设备存在这个文件路径

        Args:
            file_path (str): 文件路径

        Returns:
            bool: true 存在， false不存在
        """
        res = await self.shell("ls", file_path)
        return "No such file or directory" not in res

    def close(self):
        """关闭设备连接，释放资源"""
        super().close()
