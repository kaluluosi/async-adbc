from typing import TYPE_CHECKING, Any, AsyncGenerator, List, Optional, Union, cast

from async_adbc.service.base import Service
from async_adbc.device import Device, Status
from async_adbc.protocol.connection import Connection
from async_adbc.exceptions import DeviceNotFoundError
from async_adbc.models import DeviceStatusNotification, ForwardRule


if TYPE_CHECKING:
    from async_adbc.adbclient import ADBClient


class HostService(Service):
    """Host 服务，提供与 ADB Server 交互的功能

    请求参数 host_prefix 有 host、host-serial、host-usb、host-local 四个值
    1. host : 当devices只有一个设备的时候，将指令默认发给这个设备，如果存在多个设备，会失败
    2. host-serial: 将指令定向发送到序号serial的设备，等同于 adb -s <设备序列号>
    3. host-usb : 只有一台设备以usb连接的时候，将指令默认发给这个usb设备，adb命令中没有对应的用法
    4. host-local: 只有一台模拟器设备连接的时候，将指令默认发给这个模拟器设备，adb命令没有对应的用法
    1其实同时包含了3、4的规则，为的就是敲adb命令的时候能够有个默认设备去执行指令，比如adb shell，调用默认设备的shell命令。
    我们的ADBClient就不需要这么麻烦，我们只区分host和serial，host是用于设备无关服务，serial则是用于设备有关服务。
    """

    HOST = "host"
    """host 前缀"""
    HOST_SERIAL = "host-serial"
    """host-serial 前缀"""

    async def version(self) -> int:
        """获取 ADB Server 版本号

        等同于：adb version

        Returns:
            int: 版本号
        """
        res = await self.request(self.HOST, "version")
        txt = await res.text()
        return int(txt, 16)

    async def kill(self):
        """杀死 ADB Server 进程

        等同于：adb kill-server
        """
        await self.request(self.HOST, "kill")

    async def devices(self, status: Status = Status.DEVICE) -> List[Device]:
        """获取设备列表

        等同于：adb devices / adb devices-l

        Args:
            status: 设备状态过滤，默认只返回 DEVICE 状态的设备

        Returns:
            List[Device]: 设备列表
        """
        res = await self.request(self.HOST, "devices-l")
        with res:
            ret = await res.text()

        lines = ret.splitlines()

        devices = []
        devices_infos = [line.split() for line in lines if line]
        for device_info in devices_infos:
            if device_info[1] == status.value:
                adbc = cast("ADBClient", self)
                devices.append(Device(adbc, device_info[0]))
        return devices

    async def device(
        self, serialno: Optional[str] = None, status: Status = Status.DEVICE
    ) -> Device:
        """获取指定序列号的设备

        Args:
            serialno: 设备序列号，为 None 时返回第一个设备
            status: 设备状态过滤

        Returns:
            Device: 设备对象

        Raises:
            DeviceNotFoundError: 设备不存在时抛出
        """
        devices = await self.devices(status)

        if serialno is None and devices:
            return devices[0]

        for dev in devices:
            if dev.serialno == serialno:
                return dev
        raise DeviceNotFoundError(serialno)

    async def devices_track(self) -> AsyncGenerator[DeviceStatusNotification, Any]:
        """跟踪设备状态变化

        可以循环读取这个异步生成器，一旦设备状态改变就会返回一个通知消息

        Yields:
            DeviceStatusNotification: 设备状态通知
        """
        res = await self.request(self.HOST, "track-devices")

        with res:
            async for notify in res.trace_text():
                if notify:
                    notify = notify.strip()
                    notify = notify.split()
                    yield DeviceStatusNotification(
                        serialno=notify[0], status=Status(notify[1])
                    )

    async def transport(self, serialno: str) -> Connection:
        """创建转发连接

        转发模式下的连接发送的请求都会直接转发到 Android 设备的 adbd 进程

        此方法是实现 LOCAL SERVICE 的核心方法

        Args:
            serialno: 设备序列号

        Returns:
            Connection: 已切换到传输模式的连接
        """
        conn = await self.create_connection()
        await conn.transport_mode(serialno)
        return conn

    async def remote_connect(self, host: str, port: int) -> bool:
        """远程连接设备

        等同于：adb connect host:port

        注意：Android 设备要先用 adb tcpip 开启远程调试端口后才能 connect，本方法不会帮开调试端口

        Args:
            host: 主机 IP
            port: 端口

        Returns:
            bool: True 连接成功，False 连接失败
        """
        res = await self.request(self.HOST, "connect", host, str(port))
        with res:
            result = await res.text()
            return "connected" in result

    async def remote_disconnect(self, host: str, port: int):
        """断开远程设备

        等同于：adb disconnect host:port

        Args:
            host: 主机 IP
            port: 端口

        Returns:
            str: 返回信息
        """
        res = await self.request(self.HOST, "disconnect", host, str(port))
        with res:
            return await res.text()

    async def forward_list(self) -> List[ForwardRule]:
        """列出当前主机所有的转发规则列表

        等同于：adb forward --list

        Returns:
            List[ForwardRule]: 转发规则列表
        """
        res = await self.request(self.HOST, "list-forward")
        res = await res.text()
        lines = res.splitlines()

        rules = []
        for line in lines:
            if line:
                serialno, local, remote = line.split()
                rules.append(ForwardRule(serialno=serialno, local=local, remote=remote))
        return rules

    async def forward(
        self, serialno: str, local: str, remote: str, norebind: bool = False
    ):
        """端口映射 / 正向代理

        等同于：adb forward <local> <remote>

        Args:
            serialno: 设备序列号
            local: 本地地址
            remote: 远程地址
            norebind: 是否不重新绑定
        """
        if norebind:
            res = await self.request(
                self.HOST_SERIAL, serialno, "forward", "norebind", f"{local};{remote}"
            )
        else:
            res = await self.request(
                self.HOST_SERIAL, serialno, "forward", f"{local};{remote}"
            )
        res.close()

    async def forward_remove(self, serialno: str, local: Union[str, ForwardRule]):
        """移除端口映射

        等同于：adb forward --remove <local>

        Args:
            serialno: 设备序列号
            local: 本地地址
        """
        if isinstance(local, ForwardRule):
            local = local.local

        res = await self.request(self.HOST_SERIAL, serialno, "killforward", local)
        res.close()

    async def forward_remove_all(self):
        """移除所有设备所有端口映射

        等同于：adb forward --remove-all
        """
        res = await self.request(self.HOST, "killforward-all")
        res.close()
