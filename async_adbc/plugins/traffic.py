import typing
from async_adbc.plugin import Plugin
from pydantic import BaseModel

if typing.TYPE_CHECKING:
    from async_adbc.device import Device


class TrafficStat(BaseModel):
    """
    流量统计，单位byte

    _extended_summary_
    """

    receive: float
    send: float

    def __sub__(self, other: "TrafficStat"):
        receive = self.receive - other.receive
        send = self.send - other.send
        return TrafficStat(receive=receive, send=send)

    def __add__(self, other: "TrafficStat"):
        receive = self.receive + other.receive
        send = self.send + other.send
        return TrafficStat(receive=receive, send=send)


class TrafficPlugin(Plugin):
    def __init__(self, device: "Device") -> None:
        super().__init__(device)

    async def gloabal_stat(self) -> TrafficStat:
        """
        异步获取设备的网络流量统计信息。

        该方法通过在设备上执行shell命令来获取网络接口的接收和发送字节数。
        单位是字节（byte）。

        Returns:
            TrafficStat: 包含接收和发送字节数的TrafficStat对象。
        """
        # 获取设备上所有网络接口的接收字节数（不包括环回接口lo）
        # 单位是 byte
        prev_rx = await self._device.shell(
            r"""cat /proc/net/dev | awk 'NR>2 {if ($1 ~ /:/) {sub(":","",$1); if ($1 != "lo") rx += $2}} END {print rx}'"""
        )

        # 获取设备上所有网络接口的发送字节数（不包括环回接口lo）
        # 单位是 byte
        prev_tx = await self._device.shell(
            r"""cat /proc/net/dev | awk 'NR>2 {if ($1 ~ /:/) {sub(":","",$1); if ($1 != "lo") tx += $10}} END {print tx}'"""
        )

        # 创建TrafficStat对象，包含接收和发送的字节数
        stat = TrafficStat(receive=float(prev_rx), send=float(prev_tx))

        # 返回网络流量统计信息
        return stat

    async def app_stat(self, package_name: str) -> TrafficStat:
        """
        异步获取指定应用的网络流量统计信息。

        参数:
            package_name (str): 应用的包名。

        返回:
            TrafficStat: 包含接收和发送字节数的流量统计对象。

        异常:
            ValueError: 如果找不到指定的包名，则抛出该异常。
        """
        # 通过包名获取应用的进程ID
        pid = await self._device.get_pid_by_pkgname(package_name)
        if pid is None:
            # 如果找不到包名，抛出异常
            raise ValueError("Package not found")

        # 获取应用的上一次接收字节数
        prev_rx = await self._device.shell(
            r"""cat /proc/"""
            + str(pid)
            + """/net/dev | awk 'NR>2 {if ($1 ~ /:/) {sub(":","",$1); if ($1 != "lo") rx += $2}} END {print rx}'"""
        )

        # 获取应用的上一次发送字节数
        prev_tx = await self._device.shell(
            r"""cat /proc/"""
            + str(pid)
            + """/net/dev | awk 'NR>2 {if ($1 ~ /:/) {sub(":","",$1); if ($1 != "lo") tx += $10}} END {print tx}'"""
        )

        # 创建TrafficStat对象，包含接收和发送的字节数
        stat = TrafficStat(receive=float(prev_rx), send=float(prev_tx))

        # 返回网络流量统计信息
        return stat
