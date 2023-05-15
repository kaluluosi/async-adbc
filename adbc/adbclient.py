import asyncio
import functools
from types import MethodType
from typing import Any, AsyncGenerator
from adbc.device import Device, Status
from adbc.protocol import create_connection
from dataclasses import dataclass
from dataclasses_json import dataclass_json


class DeviceNotFoundError(Exception):
    def __init__(self, serialno: str, *args: object) -> None:
        super().__init__(f"{serialno} 不存在", *args)


@dataclass_json
@dataclass
class DeviceStatusNotification:
    serialno: str
    status: Status


@dataclass_json
@dataclass
class ProxyRule:
    serialno: str
    local: str
    remote: str


class ADBClient:
    """
    adb的命令分为两部分
    1. 一部分是ADBClient Host服务，例如 `adb version` `adb devices`，这类指令不依赖设备，属于ADBClient自己的功能。
    2. 另一部分是Device服务，例如 如果adb只有一个设备连接的情况 `adb shell` 其实等同于 `adb -s <第一个设备序号> shell`，这时候可以省略`-s`参数。

    请求参数host-prefix 有 host、host-serial、host-usb、host-local三个值
    1. host : 当devices只有一个设备的时候，将指令默认发给这个设备，如果存在多个设备，会失败
    2. host-serial： 将指令定向发送到序号serial的设备， 等同于 `adb -s <设备序号>`
    3. host-usb: 只有一台设备以usb连接时，将指令默认发给这个usb设备， adb命令中没有对应的用法
    4. host-local：只有一台模拟器设备连接的时候，将指令默认发给这个模拟器设备，adb命令没有对应的用法

    1其实同时包含了3、4的规则，为的就是敲adb指令的时候能够有个默认设备去执行指令，例如`adb shell`，调用默认设备的shell命令。
    我们的ADBClient就不需要这么麻烦，我们只区分hsot和serial，host是用于设备无关服务，serial则是用于设备有关服务。

    """

    device_class = Device

    def __init__(self, host: str = "127.0.0.1", port: int = 5037) -> None:
        if host == "localhost":
            raise Warning(
                "localhost会因为本地DNS解析的关系严重影响请求响应速度"
                "会导致一个本地连接需要2000ms才能建立，因此建议改用'127.0.0.1'"
            )

        self.host = host
        self.port = port

    async def create_connection(self):
        return await create_connection(self.host, self.port)

    async def request(self, *args):
        conn = await create_connection(self.host, self.port)
        return await conn.request(*args)

    async def version(self):
        """
        等同 adb version
        """
        res = await self.request("host", "version")
        txt = await res.text()
        return int(txt, 16)

    async def devices(self, status: Status = Status.DEVICE) -> list[Device]:
        """
        等同 adb devies/devices-l
        """
        devices: list[self.device_class] = []
        res = await self.request("host", "devices-l")
        res = await res.text()
        lines = res.split("\n")
        devices_infos = [line.split() for line in lines if line]
        for device_info in devices_infos:
            if device_info[1] == status.value:
                devices.append(self.device_class(self, device_info[0]))
        return devices

    async def device(self, serialno: str) -> Device:
        """获取指定serialno的设备

        Args:
            serialno (str): 序列号

        Raises:
            DeviceNotFoundError: 设备不存在时抛出

        Returns:
            Device: 安卓设备对象
        """
        devices = await self.devices()
        for dev in devices:
            if dev.serialno == serialno:
                return dev
        raise DeviceNotFoundError(serialno)

    async def devices_track(self) -> AsyncGenerator[DeviceStatusNotification, Any]:
        """追踪设备状态，可以循环读取这个一部生成器，一旦设备状态改编就会返回一个通知消息。

        Returns:
            AsyncGenerator[DeviceStatusNotification, Any]: 设备状态消息生成器

        Yields:
            Iterator[AsyncGenerator[DeviceChangedNotification, Any]]: 状态消息
        """
        res = await self.request("host", "track-devices")
        async for notify in res.trace_text():
            if notify:
                notify = notify.strip()
                notify = notify.split()
                yield DeviceStatusNotification(notify[0], Status(notify[1]))

    async def remote_connect(self, host: str, port: int) -> bool:
        """远程连接设备
        等同 adb connect
        注意：android设备要先用adb tcpip开启远程调试端口后才能connect，本方法不会帮开调试端口
        Args:
            host (str): ip
            port (int): 端口

        Returns:
            bool: true成功，false失败
        """
        res = await self.request("host", "connect", host, port)
        result = await res.text()
        return "connected" in result

    async def remote_disconnect(self, host: str, port: int):
        """断开远程设备
        等同 adb disconnect
        Args:
            host (str): ip
            port (int): 端口

        Returns:
            bool: 返回信息
        """
        res = await self.request("host", "disconnect", host, port)
        return await res.text()

    async def forward_list(self) -> dict[str, str]:
        """
        列出当前主机所有的转发规则列表
        adb forward 添加转发的接口在Device对象里，ADBClient只有查看所有转发列表的功能
        等同 adb forward --list
        """
        res = await self.request("host", "list-forward")
        res = await res.text()
        lines = res.splitlines()

        rules: list[ProxyRule] = []

        for line in lines:
            if line:
                serialno, local, remote = line.split()
                rules.append(ProxyRule(serialno, local, remote))

        return rules

    async def forward(
        self, serialno: str, local: str, remote: str, norebind: bool = False
    ):
        """端口映射/正向代理
        等同 adb forward

        Asks the ADB server to forward local connections from <local>
        to the <remote> address on a given device.
        There, <host-prefix> can be one of the
        host-serial/host-usb/host-local/host prefixes as described previously
        and indicates which device/emulator to target.

        the format of <local> is one of:
        tcp:<port>      -> TCP connection on localhost:<port>
        local:<path>    -> Unix local domain socket on <path>
        the format of <remote> is one of:
        tcp:<port>      -> TCP localhost:<port> on device
        local:<path>    -> Unix local domain socket on device
        jdwp:<pid>      -> JDWP thread on VM process <pid>
        vsock:<CID>:<port> -> vsock on the given CID and port

        Args:
            serialno (str): 设备序号
            local (str): 本地端口 有多种格式
            remote (str): 远程端口 有多种格式
            norebind (bool, optional): 不重复绑定. Defaults to False.
        """
        if norebind:
            await self.request(
                "host-serial", serialno, "forward", "norebind", f"{local};{remote}"
            )
        else:
            await self.request("host-serial", serialno, "forward", f"{local};{remote}")

    async def forward_remove(self, serialno: str, local: str):
        """移除端口映射
        等同 adb forward --remove

        Args:
            serialno (str): 设备序号
            local (str): 本地端口
        """
        await self.request("host-serial", serialno, "killforward", local)

    async def forward_remove_all(self, serialno: str):
        """移除所有端口映射
        等同 adb forward --remove-all

        Args:
            serialno (str): 设备序号
        """
        await self.request("host-serial", serialno, "killforward-all")

    async def reverse_list(self, serialno: str) -> list[ProxyRule]:
        res = await self.request("host", "reverse:list-forward")
        res = await res.text()
        lines = res.splitlines()

        rules: list[ProxyRule] = []

        for line in lines:
            if line:
                serialno, remote, local = line.split()
                lines.append(ProxyRule(serialno, local, remote))
        return rules

    async def reverse_forward(
        self, serialno: str, remote: str, local: str, norebind: bool
    ):
        pass
