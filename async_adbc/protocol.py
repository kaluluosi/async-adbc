import asyncio
from asyncio import StreamReader, StreamWriter
import struct
from typing import Any, AsyncGenerator, Iterable

# adb协议相关参考
# ref https://github.com/kaluluosi/adbDocumentation/blob/master/README.zh-cn.md
# 本工具包的实现参考了ppadb 鸣谢 https://github.com/Swind/pure-python-adb


HEADER_LENGTH = 4

# Messages
# adb底层消息指令
OKAY = "OKAY"  # 命令成功时的返回
FAIL = "FAIL"  # 命令失败的时候的返回
STAT = "STAT"  # 获取文件属性（大小、mode、修改日期）
LIST = "LIST"  # 列出目录下所有文件  - 我们有 shell ls 命令比这个好用，所以不用实现
DENT = "DENT"  # LIST指令的返回响应  - 同上，这个命令是跟LIST配套的
RECV = "RECV"  # 设置要拉取的文件路径src
SEND = "SEND"  # 文件发送前,设置src和dest参数
DATA = "DATA"  # 紧接上面协议，发送文件数据块
DONE = "DONE"  # 文件发送完毕后的通知服务器结束
QUIT = "QUIT"  # 退出


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


class Response:
    def __init__(self, reader: StreamReader) -> None:
        self._reader = reader

    @property
    def reader(self):
        """一些命令没有响应但是有文本输出，需要直接用reader读取。
        比如：LocalService的Shell命令

        Returns:
            _type_: _description_
        """
        return self._reader

    async def text(self) -> str:
        """获取响应结果

        Returns:
            str: 结果字符串
        """
        recv = await self.byte()
        return recv.decode()

    async def byte(self) -> bytes:
        header = await self.reader.read(HEADER_LENGTH)
        nob = int(header.decode(), 16)
        recv = await self.reader.read(nob)
        return recv

    async def trace(self) -> AsyncGenerator[bytes, Any]:
        """
        持续返回响应数据
        """
        try:
            while True:
                data = await self.byte()
                yield data
        except:
            pass

    async def trace_text(self) -> AsyncGenerator[str, Any]:
        """
        持续返回响应数据文本
        """
        recv: bytes
        async for recv in self.trace():
            yield recv.decode()


class Connection:
    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.reader = reader
        self.writer = writer

    async def request(self, *args: str):
        """service的请求接口，这个接口专门用来发送 `host:version`这类service协议

        Args:
            msg (str): _description_

        Returns:
            _type_: _description_
        """

        msg = ":".join([str(arg) for arg in args])
        data = pack(msg)
        self.writer.write(data)
        await self.writer.drain()
        await self._check_status()
        return Response(self.reader)

    async def message(self, MSG: str, length: int | None = None, data: bytes = b""):
        """底层message协议请求接口，用于发送OKAY、SEND等文件传输协议

        Args:
            MSG (str): OKAY、SEND等
        """

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
        """
        转发模式，调用后，connection直接把请求转发到设备adbd进程上
        """
        cmd = f"host:transport:{serialno}"
        await self.request(cmd)
        return self
