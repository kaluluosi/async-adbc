import typing
from async_adbc.plugin import Plugin
from typing import Optional, overload
from pydantic import BaseModel
from functools import lru_cache

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

    @lru_cache
    def _get_app_traffic_straight(self):
        UID_STAT_FILE = "/proc/uid_stat"

        if self._device.file_exists(UID_STAT_FILE):
            # 优先采用UID_STAT方案获取APP流量
            async def _uid_stat_traffic(package_name: str):
                uid = await self._device.get_uid_by_package_name(package_name)
                UID_STAT_RCV = f"/proc/uid_stat/{uid}/tcp_rcv"
                UID_STAT_SND = f"/proc/uid_stat/{uid}/tcp_snd"
                rcv = await self._device.shell(f"cat {UID_STAT_RCV}")
                snd = await self._device.shell(f"cat {UID_STAT_SND}")
                stat = TrafficStat(receive=int(rcv), send=int(snd))
                return stat

            return _uid_stat_traffic

        elif self._device.file_exists("/proc/net/xt_qtaguid/stats"):
            # 尝试用xt_qtaguid方案获取APP流量
            async def _xt_qtguid_traffic(package_name: str):
                uid = await self._device.get_uid_by_package_name(package_name)
                xt_qtguid_rcv = f"/proc/net/xt_qtaguid/stats| grep {uid}"
                data = await self._device.shell(xt_qtguid_rcv)
                total_rcv = 0
                total_snd = 0
                lines = data.splitlines()
                for line in lines:
                    seq = line.split()
                    rcv = int(seq[5])
                    snd = int(seq[7])
                    total_rcv += rcv
                    total_snd += snd

                stat = TrafficStat(receive=total_rcv, send=total_snd)
                return stat

            return _xt_qtguid_traffic

        else:
            # 如果上面两个方案的文件都找不到，就抛出异常
            raise FileNotFoundError("文件找不到")

    async def _get_app_traffic(self, package_name: str):
        straight = self._get_app_traffic_straight()
        return await straight(package_name)

    async def _get_global_traffic(self):
        """
        获取全局流量

        NOTE: 所有网卡累加，并且获取到的是设备启动以来的总流量

        Returns:
            TrafficStat: 流量
        """
        result = await self._device.shell("cat /proc/net/dev")
        lines = map(lambda line: line.split(), result.splitlines()[2:])
        for line in lines:
            receive = int(line[0])
            send = int(line[8])
            stat = TrafficStat(receive=receive, send=send)
            return stat

    @overload
    async def stat(self):
        """
        获取全局流量

        Returns:
            TrafficStat: 流量
        """
        ...

    @overload
    async def stat(self, package_name: str):
        """
        获取根据某个报名获取流量

        Args:
            package_name (str): 包名

        Returns:
            TrafficStat: 流量
        """
        ...

    async def stat(self, package_name: Optional[str] = None):
        """
        获取流量，单位 `byte`

        NOTE:
            默认获取全局流量，读取的是`/proc/net/dev`，也就是自设备启动以来的所有网卡累计流量。

            APP流量则采用 `uid_stat`，`xt_qtaguid` 两种方案读取。

        WARNING: 如果获取流量失败那么默认会返回一0流量

        Args:
            package_name (Optional[str], optional): 不传就获取全局流量. Defaults to None.

        Returns:
            TrafficStat: 流量统计
        """
        try:
            if package_name is None:
                return await self._get_global_traffic()
            else:
                return await self._get_app_traffic(package_name)
        except Exception:
            return TrafficStat()
