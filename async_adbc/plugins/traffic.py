import typing
from async_adbc.plugin import Plugin
from typing import Optional, overload
from pydantic import BaseModel

if typing.TYPE_CHECKING:
    from async_adbc.device import Device


class TrafficStat(BaseModel):
    """
    流量统计，单位byte
    """

    receive: float = 0
    send: float = 0

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
        self._last_stat: Optional[TrafficStat] = None

    async def _get_global_traffic(self):
        """
        获取全局流量

        NOTE: 所有网卡累加，并且获取到的是设备启动以来的总流量

        Returns:
            TrafficStat: 流量
        """
        result = await self._device.shell("cat /proc/net/dev")
        lines = map(lambda line: line.split(), result.splitlines()[2:])

        rcv = 0
        snd = 0
        for line in lines:
            rcv += int(line[1])
            snd += int(line[9])

        stat = TrafficStat(receive=rcv, send=snd)
        return stat

    @overload
    async def stat(self) -> TrafficStat:
        """
        获取全局流量

        Returns:
            TrafficStat: 流量
        """
        ...

    @overload
    async def stat(self, package_name: str) -> TrafficStat:
        """
        获取根据某个报名获取流量

        Args:
            package_name (str): 包名

        Returns:
            TrafficStat: 流量
        """
        ...

    async def stat(self, package_name: Optional[str] = None) -> TrafficStat:
        """
        获取流量，单位 `byte`

        NOTE:
            默认获取全局流量，读取的是`/proc/net/dev`，也就是自设备启动以来的所有网卡累计流量。

            APP流量则采用 `uid_stat`，`xt_qtaguid` 两种方案读取。

        WARNING: 目前package_name参数是无效的，返回的依旧是全局流量。

        Args:
            package_name (Optional[str], optional): 不传就获取全局流量. Defaults to None.

        Returns:
            TrafficStat: 流量统计
        """

        # XXX:
        # 单纯靠adb读文件的方式无法兼容性很好的获取应用程序流量
        # [1] `/proc/uid_stat/$uid/tcp_rcv`` 和 `/proc/uid_stat/$uid/tcp_snd`,兼容性差，很多手机没有这个文件
        # [2] `/proc/$pid/net/dev`，表面上每个进程id一个文件，然而实际上读取到的是全局流量
        # [3] `/proc/net/xt_qtaguid/stats`，只在Android9.0及其以下有这个文件
        # [4] `/sys/fs/bpf/traffic_uid_stats_map`，支持Android10.0以上，但是需要root权限

        # TODO: 最后一个方案， 学习Android开发，开发一个AndroidService的jar包，这个jar包运行一个服务器，使用系统接口获取
        # 流量，然后这个接口通过跟运行在手机上的这个服务器通信获取应用流量。
        return await self._get_global_traffic()
