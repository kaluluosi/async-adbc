import asyncio
import enum
import re
import typing
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

    async def create_connection(self) -> Connection:
        conn = await self.adbc.create_connection()
        await conn.transport_mode(self.serialno)
        return conn

    async def wait_boot_complete(
        self, timeout: int = 60, wait_interval: int = 1
    ) -> bool:
        """
        等待到重启完毕工具函数

        纯工具函数，并不是adb的指令。

        :param timeout: second
        :param timedelta: second
        """
        while timeout:
            try:
                res = await self.shell("echo", "hello")
                if res == "hello":
                    return True
            except:
                pass

            await asyncio.sleep(wait_interval)
            timeout -= 1

        raise TimeoutError("超时也没有重启完毕")

    @property
    async def properties(self) -> dict[str, str]:
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
        result = await self.shell(f"ps -e| grep -i {package_name}")

        if result:
            return int(result.split()[1])

        else:
            raise ValueError(f"{package_name} 应用没有运行")
