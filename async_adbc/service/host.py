import abc
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Union

from dataclasses_json import dataclass_json
from async_adbc.service import Service
from async_adbc.device import Device, Status
from async_adbc.protocol import Connection


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
class ForwardRule:
    serialno: str
    local: str
    remote: str


class HostService(Service):
    """
    请求参数host-prefix 有 host、host-serial、host-usb、host-local三个值
    1. host : 当devices只有一个设备的时候，将指令默认发给这个设备，如果存在多个设备，会失败
    2. host-serial： 将指令定向发送到序号serial的设备， 等同于 `adb -s <设备序号>`
    3. host-usb: 只有一台设备以usb连接时，将指令默认发给这个usb设备， adb命令中没有对应的用法
    4. host-local：只有一台模拟器设备连接的时候，将指令默认发给这个模拟器设备，adb命令没有对应的用法
    1其实同时包含了3、4的规则，为的就是敲adb指令的时候能够有个默认设备去执行指令，例如`adb shell`，调用默认设备的shell命令。
    我们的ADBClient就不需要这么麻烦，我们只区分hsot和serial，host是用于设备无关服务，serial则是用于设备有关服务。
    """

    HOST = "host"  # 当devices只有一个设备的时候，将指令默认发给这个设备，如果存在多个设备，会失败
    HOST_SERIAL = "host-serial"  # 将指令定向发送到序号serial的设备， 等同于 `adb -s <设备序号>`
    # HOST_USB = "host-usb"  # 只有一台设备以usb连接时，将指令默认发给这个usb设备， adb命令中没有对应的用法
    # HOST_LOCAL = "host-local"  # 只有一台模拟器设备连接的时候，将指令默认发给这个模拟器设备，adb命令没有对应的用法

    async def version(self) -> int:
        """
        获取adb server版本号

        等同：adb version

        Ask the ADB server for its internal version number.

        Returns:
            int: 版本号
        """

        res = await self.request(self.HOST, "version")
        txt = await res.text()
        return int(txt, 16)

    async def kill(self):
        """
        杀死adb server进程

        等同：adb kill-server

        Ask the ADB server to quit immediately. This is used when the
        ADB client detects that an obsolete server is running after an
        upgrade.
        """
        await self.request(self.HOST, "kill")

    async def devices(self, status: Status = Status.DEVICE) -> list[Device]:
        """
        获取设备列表

        等同：adb devies/devices-l

        Ask to return the list of available Android devices and their
        state. devices-l includes the device paths in the state.
        After the OKAY, this is followed by a 4-byte hex len,
        and a string that will be dumped as-is by the client, then
        the connection is closed
        """
        devices: list[Device] = []
        res = await self.request(self.HOST, "devices-l")
        res = await res.text()
        lines = res.split("\n")
        devices_infos = [line.split() for line in lines if line]
        for device_info in devices_infos:
            if device_info[1] == status.value:
                devices.append(Device(self, device_info[0]))
        return devices

    async def device(
        self, serialno: str | None = None, status: Status = Status.DEVICE
    ) -> Device:
        """获取指定serialno的设备

        Args:
            serialno (str|None): 序列号，为None时返回第一个设备

        Raises:
            DeviceNotFoundError: 设备不存在时抛出

        Returns:
            Device: 安卓设备对象
        """
        devices = await self.devices(status)

        if serialno is None and devices:
            return devices[0]

        for dev in devices:
            if dev.serialno == serialno:
                return dev
        raise DeviceNotFoundError(serialno)

    async def devices_track(self) -> AsyncGenerator[DeviceStatusNotification, Any]:
        """追踪设备状态，可以循环读取这个一部生成器，一旦设备状态改编就会返回一个通知消息。

        可以轻易的做到跟踪设备状态变更的通知

        等同：adb没有实现

        This is a variant of host:devices which doesn't close the
        connection. Instead, a new device list description is sent
        each time a device is added/removed or the state of a given
        device changes (hex4 + content). This allows tools like DDMS
        to track the state of connected devices in real-time without
        polling the server repeatedly.
        Returns:
            AsyncGenerator[DeviceStatusNotification, Any]: 设备状态消息生成器

        Yields:
            Iterator[AsyncGenerator[DeviceChangedNotification, Any]]: 状态消息
        """
        res = await self.request(self.HOST, "track-devices")
        async for notify in res.trace_text():
            if notify:
                notify = notify.strip()
                notify = notify.split()
                yield DeviceStatusNotification(notify[0], Status(notify[1]))

    async def transport(self, serialno: str) -> Connection:
        """
        创建转发连接
        转发模式下的连接发送的请求都会直接转发到Android设备的adbd进程。
        此方法是实现LOCAL SERVICE的核心方法。

        Ask to switch the connection to the device/emulator identified by
        <serial-number>. After the OKAY response, every client request will
        be sent directly to the adbd daemon running on the device.
        (Used to implement the -s option)
        """
        conn = await self.create_connection()
        await conn.transport_mode(serialno)
        return conn

    async def remote_connect(self, host: str, port: int) -> bool:
        """远程连接设备
        等同：adb connect
        注意：android设备要先用adb tcpip开启远程调试端口后才能connect，本方法不会帮开调试端口
        Args:
            host (str): ip
            port (int): 端口

        Returns:
            bool: true成功，false失败
        """
        res = await self.request(self.HOST, "connect", host, port)
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
        res = await self.request(self.HOST_SERIAL, "disconnect", host, port)
        return await res.text()

    async def forward_list(self) -> list[ForwardRule]:
        """
        列出当前主机所有的转发规则列表
        adb forward 添加转发的接口在Device对象里，ADBClient只有查看所有转发列表的功能
        等同 adb forward --list
        """
        res = await self.request(self.HOST, "list-forward")
        res = await res.text()
        lines = res.splitlines()

        rules: list[ForwardRule] = []

        for line in lines:
            if line:
                serialno, local, remote = line.split()
                rules.append(ForwardRule(serialno, local, remote))

        return rules

    async def forward(
        self, serialno: str, local: str, remote: str, norebind: bool = False
    ):
        """端口映射/正向代理
        等同：adb forward <local> <remote>

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
            norebind (bool, optional): 不重复绑定，如果发现端口已映射会抛出错误. Defaults to False.
        """
        if norebind:
            await self.request(
                self.HOST_SERIAL, serialno, "forward", "norebind", f"{local};{remote}"
            )
        else:
            await self.request(
                self.HOST_SERIAL, serialno, "forward", f"{local};{remote}"
            )

    async def forward_remove(self, serialno: str, local: Union[str, ForwardRule]):
        """移除端口映射
        等同: adb forward --remove

        Args:
            serialno (str): 设备序号
            local (str): 本地端口
        """
        if isinstance(local, ForwardRule):
            local = local.local

        await self.request(self.HOST_SERIAL, serialno, "killforward", local)

    async def forward_remove_all(self):
        """移除所有设备所有端口映射
        等同 adb forward --remove-all

        这个指令是将所有端口映射规则都删除，host、host-serial前缀效果都一样
        Args:
            serialno (str): 设备序号
        """
        await self.request(self.HOST, "killforward-all")
