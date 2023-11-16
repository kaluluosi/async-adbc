"""
adb协议文档 https://github.com/kaluluosi/adbDocumentation/blob/master/README.zh-cn.md

根据这份文档中SERVICE.TXT的描述
adb的命令分两个部分
HOST SERVICES : ADB Server提供的服务
LOCAL SERVICES：由运行在Android设备上的ADB Daemon 守护进程提供的服务

可以这么理解：

adbc是跟adb server的客户端，也就是 HOST SERVICES的封装。
device是跟adbd守护进程的客户端，也就是LOCAL SERVICES的封装。
"""


import abc

from async_adbc.protocol import Connection, Response


class Service(abc.ABC):
    @abc.abstractmethod
    async def create_connection(self) -> Connection:
        ...

    async def request(self, *args:str)->Response:
        conn = await self.create_connection()
        return await conn.request(*args)
    
    async def request_without_check(self,*args:str) -> Response:
        conn = await self.create_connection()
        return await conn.request_without_check(*args)

