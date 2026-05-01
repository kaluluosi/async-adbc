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
        # 不再共享连接，每次请求创建新连接，避免 ConnectionResetError
        pass

    @abc.abstractmethod
    async def create_connection(self) -> Connection:
        ...

    def close(self):
        # 不再有共享连接需要关闭
        pass

    async def request(self, *args: str) -> Response:
        conn = await self.create_connection()
        try:
            return await conn.request(*args)
        except Exception:
            conn.close()
            raise

    async def request_without_check(self, *args: str) -> Response:
        conn = await self.create_connection()
        try:
            return await conn.request_without_check(*args)
        except Exception:
            conn.close()
            raise
