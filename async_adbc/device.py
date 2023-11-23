import enum
import re
import typing

from async_lru import alru_cache
from async_adbc.protocol import Connection
from async_adbc.service.local import LocalService

from async_adbc.plugins import (
    PMPlugin,
    PropPlugin,
    CPUPlugin,
    GPUPlugin,
    BatteryPlugin,
    FpsPlugin,
    MemPlugin,
    TempPlugin,
    UtilsPlugin,
    TrafficPlugin,
    ForwardPlugin,
    ActivityManagerPlugin,
    LogcatPlugin,
    MinicapPlugin,
    WMPlugin,
    InputPlugin,
)


if typing.TYPE_CHECKING:
    from async_adbc.adbclient import ADBClient


class Status(enum.Enum):
    DEVICE = "device"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class Device(LocalService):
    def __init__(self, adbc: "ADBClient", serialno: str) -> None:
        self.adbc = adbc
        self.serialno = serialno

        self.pm = PMPlugin(self)
        self.prop = PropPlugin(self)
        self.cpu = CPUPlugin(self)
        self.gpu = GPUPlugin(self)
        self.mem = MemPlugin(self)
        self.fps = FpsPlugin(self)
        self.battery = BatteryPlugin(self)
        self.temp = TempPlugin(self)
        self.utils = UtilsPlugin(self)
        self.traffic = TrafficPlugin(self)
        self.am = ActivityManagerPlugin(self)
        self.forward = ForwardPlugin(self)
        self.logcat = LogcatPlugin(self)
        self.minicap = MinicapPlugin(self)
        self.wm = WMPlugin(self)
        self.input = InputPlugin(self)

    async def create_connection(self) -> Connection:
        conn = await self.adbc.create_connection()
        await conn.transport_mode(self.serialno)
        return conn

    @property
    @alru_cache
    async def properties(self) -> typing.Dict[str, str]:
        """获取设备props

        一些插件要用到所以挪到device里

        Returns:
            dict[str, str]: _description_
        """
        res = await self.shell("getprop")
        result_pattern = "^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$"  # type: ignore
        lines = res.splitlines()
        properties = {}
        for line in lines:
            m = re.match(result_pattern, line)
            if m:
                properties[m.group(1)] = m.group(2)

        return properties

    async def get_pid_by_pkgname(self, package_name: str) -> int:
        result = await self.shell(f"ps -ef| grep {package_name}")
        if result:
            lines = [
                line.split()
                for line in result.splitlines()
                if not line.startswith("shell")
            ]

            if not lines:
                raise ValueError(f"{package_name} 应用没有运行")

            process_list = [(seq[1], seq[7]) for seq in lines]
            process_list.sort(key=lambda v: v[1], reverse=False)

            return int(process_list[0][0])

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
