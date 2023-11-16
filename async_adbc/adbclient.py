from async_adbc.protocol import Connection, create_connection


from async_adbc.service.host import HostService


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5037

class ADBClient(HostService):
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        super().__init__()
        self.host = host
        self.port = port

    async def create_connection(self) -> Connection:
        conn = await create_connection(self.host, self.port)
        return conn
