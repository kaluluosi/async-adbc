from async_adbc.device import Status
from async_adbc.protocol import Connection, create_connection
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from async_adbc.service.host import HostService


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5037


class DeviceNotFoundError(Exception):
    def __init__(self, serialno: str, *args: object) -> None:
        super().__init__(f"{serialno} 不存在", *args)


@dataclass_json
@dataclass
class DeviceStatusNotification:
    serialno: str
    status: Status


@dataclass_json
@dataclass
class ForwardRule:
    serialno: str
    local: str
    remote: str


class ADBClient(HostService):
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        super().__init__()
        self.host = host
        self.port = port

    async def create_connection(self) -> Connection:
        conn = await create_connection(self.host, self.port)
        return conn
