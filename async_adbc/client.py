from async_adbc.protocol import Connection, create_connection
from async_adbc.service.host import HostService
from async_adbc.config import DEFAULT_HOST, DEFAULT_PORT


class ADBClient(HostService):
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        super().__init__()
        self.host = host
        self.port = port

    async def create_connection(self) -> Connection:
        conn = await create_connection(self.host, self.port)
        return conn
