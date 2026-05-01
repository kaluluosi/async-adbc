import asyncio
import struct
from asyncio import StreamReader, StreamWriter
from typing import Optional

from .consts import HEADER_LENGTH, OKAY
from .response import Response


def encode_length(length: int) -> bytes:
    return f"{length:04X}".encode("utf-8")


def decode_length(data: bytes) -> int:
    s_length = data.decode("utf-8")
    return int(s_length, 16)


def pack(msg: str) -> bytes:
    length = len(msg)
    b_length = encode_length(length)
    b_data = msg.encode("utf-8")
    return b_length + b_data


async def create_connection(host: str = "127.0.0.1", port: int = 5037):
    conn = await asyncio.open_connection(host, port)
    return Connection(*conn)


class Connection:
    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.reader = reader
        self.writer = writer

    async def request(self, *args: str) -> Response:
        msg = ":".join([str(arg) for arg in args])
        data = pack(msg)
        self.writer.write(data)
        await self.writer.drain()
        await self._check_status()
        return Response(self.reader, self.writer)

    async def request_without_check(self, *args: str) -> Response:
        msg = ":".join([str(arg) for arg in args])
        data = pack(msg)
        self.writer.write(data)
        await self.writer.drain()
        return Response(self.reader, self.writer)

    async def message(self, MSG: str, length: Optional[int] = None, data: bytes = b""):
        length = len(data) if length is None else length
        data = MSG.encode() + struct.pack("<I", length) + data
        self.writer.write(data)
        await self.writer.drain()

    async def _check_status(self):
        recv = await self.reader.read(HEADER_LENGTH)
        recv = recv.decode()
        if recv != OKAY:
            error = await self.reader.read(-1)
            error = error.decode()
            raise RuntimeError("ERROR: {} {}".format(repr(recv), error))
        return True

    async def transport_mode(self, serialno: str):
        cmd = f"host:transport:{serialno}"
        await self.request(cmd)
        return self

    def close(self):
        self.writer.close()

    def __enter__(self):
        pass

    def __exit__(self, *args, **kwargs):
        self.writer.close()

    async def __aenter__(self):
        pass

    async def __aexit__(self, *args, **kwargs):
        self.writer.close()
        await self.writer.wait_closed()
