import typing
from async_adbc.plugin import Plugin
from typing import Optional, overload
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
    WAN0 = "wlan0:"

    def __init__(self, device: "Device") -> None:
        super().__init__(device)
        self._last_stat: Optional[TrafficStat] = None

    @overload
    async def stat(self) -> TrafficStat:
        ...

    @overload
    async def stat(self, package_name: str) -> TrafficStat:
        ...

    async def stat(self, package_name: Optional[str] = None) -> TrafficStat:
        """获取流量

        默认获取全局流量

        单位 byte

        Args:
            package_name (Optional[str], optional): 不传就获取全局流量. Defaults to None.

        Returns:
            TrafficStat: 流量统计
        """

        try:
            if package_name:
                pid = await self._device.get_pid_by_pkgname(package_name)
                result = await self._device.shell(f"cat /proc/{pid}/net/dev")
            else:
                result = await self._device.shell("cat /proc/net/dev")
        except Exception:
            result = await self._device.shell("cat /proc/net/dev")

        lines = map(lambda line: line.split(), result.splitlines()[2:])
        table = {line[0]: line[1:] for line in lines}

        wlan0 = table[self.WAN0]
        receive = int(wlan0[0])
        send = int(wlan0[8])
        new_stat = TrafficStat(receive=receive, send=send)

        if self._last_stat is None:
            self._last_stat = new_stat

        diff = new_stat - self._last_stat
        self._last_stat = new_stat
        return diff
