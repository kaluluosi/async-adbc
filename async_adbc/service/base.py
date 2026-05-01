"""
adb协议文档 https://github.com/kaluluosi/adbDocumentation/blob/master/README.zh-cn.md

根据这份文档中SERVICE.TXT的描述
adb的命令分两个部分
HOST SERVICES : ADB Server提供的服务
LOCAL SERVICES：由运行在Android设备上的ADB Daemon 守护进程提供的服务

可以这么理解：

adbc是跟adb server的客户端，也就是HOST SERVICES的封装。
device是跟adbd守护进程的客户端，也就是LOCAL SERVICES的封装。
"""

import abc
import asyncio
from typing import Optional

from async_adbc.protocol.connection import Connection, Response


class Service(abc.ABC):
    def __init__(self):
        self._conn: Optional[Connection] = None
        self._lock = asyncio.Lock()

    @abc.abstractmethod
    async def create_connection(self) -> Connection:
        ...

    async def _get_connection(self) -> Connection:
        async with self._lock:
            if self._conn is None:
                self._conn = await self.create_connection()
            return self._conn

    def _close_connection(self):
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def close(self):
        self._close_connection()

    async def request(self, *args: str) -> Response:
        conn = await self._get_connection()
        try:
            return await conn.request(*args)
        except Exception:
            self._close_connection()
            raise

    async def request_without_check(self, *args: str) -> Response:
        conn = await self._get_connection()
        try:
            return await conn.request_without_check(*args)
        except Exception:
            self._close_connection()
            raise
