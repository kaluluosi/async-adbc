import asyncio
from asyncio import StreamReader, StreamWriter
from typing import Any, AsyncGenerator, Optional, Type


class Response:
    def __init__(self, reader: StreamReader, _writer: StreamWriter) -> None:
        self._reader = reader
        self._writer = _writer

    @property
    def reader(self):
        return self._reader

    def __enter__(self):
        pass

    def __exit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb):
        self._writer.close()

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb):
        self._writer.close()
        await self._writer.wait_closed()

    def close(self):
        self._writer.close()

    async def read(self, n: int = -1) -> bytes:
        """读取数据

        Args:
            n: 读取字节数，-1 表示读取所有

        Returns:
            bytes: 读取的数据
        """
        return await self.reader.read(n)

    async def text(self) -> str:
        try:
            recv = await self.byte()
            return recv.decode()
        except Exception:
            # 降级：直接读取所有数据
            data = await self.read()
            return data.decode()

    async def byte(self) -> bytes:
        from .consts import HEADER_LENGTH

        header = await self.reader.read(HEADER_LENGTH)
        nob = int(header.decode(), 16)
        recv = await self.reader.read(nob)
        return recv

    async def trace(self) -> AsyncGenerator[bytes, Any]:
        try:
            while True:
                data = await self.byte()
                yield data
        except Exception:
            pass

    async def trace_text(self) -> AsyncGenerator[str, Any]:
        recv: bytes
        async for recv in self.trace():
            yield recv.decode()
