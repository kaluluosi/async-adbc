from asyncio import StreamReader
import enum
import typing
from adbc.protocol import create_connection

if typing.TYPE_CHECKING:
    from adbc.adbclient import ADBClient, ForwardRule


class Status(enum.Enum):
    DEVICE = "device"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class Device:
    def __init__(self, adbc: "ADBClient", serialno: str) -> None:
        self.adbc = adbc
        self.serialno = serialno

    async def request(self, *args):
        """
        创建一个transport到设备的请求对象
        """
        conn = await self.adbc.create_connection()
        await conn.request("host", "transport", self.serialno)
        res = await conn.request(*args)
        return res

    async def shell_raw(self, cmd: str) -> bytes:
        res = await self.request("shell", cmd)
        return await res.byte()

    async def shell(self, cmd: str) -> str:
        res = await self.request("shell", cmd)
        return await res.text()

    async def shell_reader(self, cmd: str) -> StreamReader:
        res = await self.request("shell", cmd)
        return res.reader

    async def reverse_list(self) -> list[ForwardRule]:
        pass
