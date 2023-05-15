from asyncio import StreamReader
import enum
import typing
from adbc.protocol import Connection, create_connection
from adbc.service.local import LocalService

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

    async def create_connection(self) -> Connection:
        conn = await self.adbc.create_connection()
        await conn.transport_mode(self.serialno)
        return conn
