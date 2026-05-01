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
    """设备状态枚举"""

    DEVICE = "device"
    """设备已连接"""
    OFFLINE = "offline"
    """设备离线"""
    UNKNOWN = "unknown"
    """未知状态"""
    UNAUTHORIZED = "unauthorized"
    """设备未授权"""
    AUTHORIZING = "authorizing"
    """设备正在授权"""


class Device(LocalService):
    """Android 设备类，封装了与设备交互的所有功能"""

    def __init__(self, adbc: "ADBClient", serialno: str) -> None:
        """初始化 Device

        Args:
            adbc: ADBClient 实例
            serialno: 设备序列号
        """
        super().__init__()
        self.adbc = adbc
        self.serialno = serialno

        self._load_plugins()

    def _load_plugins(self):
        """加载所有已注册的插件"""
        registry = get_registry()
        for metadata in registry.get_all():
            plugin = metadata.plugin_class(self)
            setattr(self, metadata.attr_name, plugin)

    async def create_connection(self) -> Connection:
        """创建并切换到传输模式的连接

        Returns:
            Connection: 已切换到传输模式的连接
        """
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
        """通过包名获取进程 PID

        Args:
            package_name: 应用包名

        Returns:
            int: 进程 PID

        Raises:
            ValueError: 应用没有运行时抛出
        """
        result = await self.shell(f"pidof {package_name}")
        if result:
            return int(result)
        else:
            raise ValueError(f"{package_name} 应用没有运行")

    async def file_exists(self, file_path: str) -> bool:
        """判断设备上是否存在这个文件路径

        Args:
            file_path: 文件路径

        Returns:
            bool: True 存在，False 不存在
        """
        res = await self.shell("ls", file_path)
        return "No such file or directory" not in res

    def close(self):
        """关闭设备连接，释放资源"""
        super().close()
