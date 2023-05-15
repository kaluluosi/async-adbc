import asyncio
import enum
import typing
from adbc.plugins.utils import UtilsPlugin
from adbc.protocol import Connection
from adbc.service.local import LocalService

from adbc.plugins import PMPlugin
from adbc.plugins import PropPlugin

if typing.TYPE_CHECKING:
    from adbc.adbclient import ADBClient


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
        self.utils = UtilsPlugin(self)

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
            res = await self.shell("echo", "hello")
            if res == "hello":
                return True

            await asyncio.sleep(wait_interval)
            timeout -= 1

        raise TimeoutError("超时也没有重启完毕")
