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

    async def text(self) -> str:
        recv = await self.byte()
        return recv.decode()

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
