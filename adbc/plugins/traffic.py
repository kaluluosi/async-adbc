import typing
from . import Plugin
from typing import Optional, overload
from dataclasses import dataclass
from dataclasses_json import dataclass_json

if typing.TYPE_CHECKING:
    from adbc.device import Device


@dataclass_json
@dataclass
class TrafficStat:
    """
    流量统计，单位byte

    _extended_summary_
    """

    receive: float
    transmit: float

    def __sub__(self, other: "TrafficStat"):
        recive = self.receive - other.receive
        transmit = self.transmit - other.transmit
        return TrafficStat(recive, transmit)


class TrafficPlugin(Plugin):
    def __init__(self, device: "Device") -> None:
        super().__init__(device)
        self._last_stat: Optional[TrafficStat] = None
        self._last_pkg_stat: Optional[TrafficStat] = None

    @overload
    async def stat(self) -> TrafficStat:
        ...

    @overload
    async def stat(self, package_name: str) -> TrafficStat:
        ...

    async def stat(self, package_name=None):
        if isinstance(package_name, str):
            pid = self._get_pid(package_name)
            result = await self._device.shell(f"cat /proc/{pid}/net/dev")
            lines = map(lambda line: line.split(), result.splitlines()[2:])
            table = {line[0]: line[1:] for line in lines}

            wlan0 = table["wlan0:"]
            receive = int(wlan0[0])
            transmit = int(wlan0[8])
            new_stat = TrafficStat(receive, transmit)
            if self._last_pkg_stat is None:
                self._last_pkg_stat = new_stat
                return TrafficStat(0, 0)

            diff = new_stat - self._last_pkg_stat
            return diff
        else:
            result = await self._device.shell("cat /proc/net/dev")
            lines = map(lambda line: line.split(), result.splitlines()[2:])
            table = {line[0]: line[1:] for line in lines}

            wlan0 = table["wlan0:"]
            receive = int(wlan0[0])
            transmit = int(wlan0[8])
            new_stat = TrafficStat(receive, transmit)

            if self._last_stat is None:
                self._last_stat = new_stat
                return TrafficStat(0, 0)

            diff = new_stat - self._last_stat
            return diff

    async def _get_pid(self, package_name: str) -> int:
        result = await self._device.shell(f"ps -e | grep -i {package_name}")

        if result:
            return int(result.split()[1])

        else:
            raise ValueError(f"{package_name} 应用没有运行")
