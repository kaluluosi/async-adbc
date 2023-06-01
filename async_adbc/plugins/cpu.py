import asyncio
import re
import typing

from typing import Optional, overload
from dataclasses import field, dataclass
from dataclasses_json import dataclass_json

from . import Plugin

if typing.TYPE_CHECKING:
    from async_adbc.device import Device

CPUStatMap = dict[int, "CPUStat"]
CPUUsageMap = dict[int, "CPUUsage"]


@dataclass_json
@dataclass
class CPUInfo:
    platform: str
    name: str
    abi: str
    core: int
    freq: tuple[int, int]


@dataclass_json
@dataclass
class CPUUsage:
    usage: float = field(default=0.0)
    normalized: float = field(default=0.0)


@dataclass_json
@dataclass
class CPUFreq:
    min: int
    cur: int
    max: int


@dataclass_json
@dataclass
class CPUStat:
    user: float = 0
    nice: float = 0
    system: float = 0
    idle: float = 0
    iowait: float = 0
    irq: float = 0
    softirq: float = 0
    stealstolen: float = 0
    guest: float = 0
    guest_nice: float = 0

    @property
    def total(self):
        return (
            self.user
            + self.nice
            + self.system
            + self.idle
            + self.iowait
            + self.irq
            + self.softirq
            + self.stealstolen
            + self.guest
            + self.guest_nice
        )

    @property
    def usage(self) -> float:
        """
        获取占用率，单位%

        Returns:
            float: 占用率
        """
        return 100 * (self.user + self.system) / self.total

    def __add__(self, other: "CPUStat"):
        summary = CPUStat()

        summary.user = self.user + other.user
        summary.nice = self.nice + other.nice
        summary.system = self.system + other.system
        summary.idle = self.idle + other.idle
        summary.iowait = self.iowait + other.iowait
        summary.irq = self.irq + other.irq
        summary.softirq = self.softirq + other.softirq
        summary.stealstolen = self.stealstolen + other.stealstolen
        summary.guest = self.guest + other.guest
        summary.guest_nice = self.guest_nice + other.guest_nice

        return summary

    def __sub__(self, other: "CPUStat"):
        result = CPUStat()

        result.user = self.user - other.user
        result.nice = self.nice - other.nice
        result.system = self.system - other.system
        result.idle = self.idle - other.idle
        result.iowait = self.iowait - other.iowait
        result.irq = self.irq - other.irq
        result.softirq = self.softirq - other.softirq
        result.stealstolen = self.stealstolen - other.stealstolen
        result.guest = self.guest - other.guest
        result.guest_nice = self.guest_nice - other.guest_nice

        return result

    def __str__(self):
        attrs = vars(self)
        return ", ".join("%s: %s" % item for item in attrs.items())


@dataclass_json
@dataclass
class ProcessCPUStat:
    name: str = ""
    utime: int = 0
    stime: int = 0
    cutime: int = 0
    cstime: int = 0

    def __add__(self, other: "ProcessCPUStat"):
        summary = ProcessCPUStat(self.name)
        summary.utime = self.utime + other.utime
        summary.stime = self.stime + other.stime
        summary.cutime = self.cutime + other.cutime
        summary.cstime = self.cstime + other.cstime
        return summary

    def __sub__(self, other: "ProcessCPUStat"):
        result = ProcessCPUStat(self.name)
        result.utime = self.utime - other.utime
        result.stime = self.stime - other.stime
        result.cutime = self.cutime - other.cutime
        result.cstime = self.cstime - other.cstime
        return result

    def __str__(self):
        attrs = vars(self)
        return ", ".join("%s: %s" % item for item in attrs.items())

    @property
    def total(self) -> float:
        return self.utime + self.stime + self.cutime + self.stime


class CPUPlugin(Plugin):
    def __init__(self, device: "Device") -> None:
        super().__init__(device)
        self._freqs = None
        self._normalize_factor = None

    @property
    async def count(self) -> int:
        """
        获取cpu核心数

        因为核心数是一定的，为了避免每次都重复请求做了缓存

        Returns:
            int: 核心数
        """
        result = await self._device.shell("ls /sys/devices/system/cpu")
        match = re.findall(r"cpu[0-9+]", result)
        _cpu_count = len(match)
        return _cpu_count

    @property
    async def freqs(self) -> list[CPUFreq]:
        """
        获取所有cpu的 最小最大和当前频率

        单位是Hz

        Returns:
            dict[int,CPUFreq]: key是CPU编号，value是CPUFreq
        """
        if self._freqs:
            return self._freqs

        count = await self.count
        coroutines = []
        for index in range(count):
            cmd_root = f"cat /sys/devices/system/cpu/cpu{index}/cpufreq"
            min = self._device.shell(f"{cmd_root}/cpuinfo_min_freq")
            cur = self._device.shell(f"{cmd_root}/scaling_cur_freq")
            max = self._device.shell(f"{cmd_root}/cpuinfo_max_freq")

            coroutine = asyncio.gather(min, cur, max)
            coroutines.append(coroutine)

        freq_list = await asyncio.gather(*coroutines)
        self._freqs = [
            CPUFreq(int(min), int(cur), int(max)) for (min, cur, max) in freq_list
        ]

        return self._freqs

    @property
    async def normalize_factor(self) -> float:
        """
        cpu占用标准化因子，用这个因子去乘以cpu占用率就可以得到设备无关的标准化占用率

        # 标准化因子，标准化CPU占用
        # 参考：https://blog.gamebench.net/measuring-cpu-usage-in-mobile-devices

        Returns:
            float: 因子
        """
        if self._normalize_factor:
            return self._normalize_factor

        cpu_freqs = await self.freqs

        # 合计所有CPU最大频率
        total_max_freq = sum([v.max for v in cpu_freqs])

        # 找出所有在在线的CPU
        online_cmd = "cat /sys/devices/system/cpu/online"
        online = await self._device.shell(online_cmd)
        phases = [
            list(map(lambda v: int(v), sub))
            for sub in [p.split("-") for p in online.split(",")]
        ]

        # 合计所有在线CPU的当前频率
        cur_freq_sum = 0
        for p in phases:
            for i in range(p[0], p[1] + 1):
                cur_freq_sum += cpu_freqs[i].cur

        self._normalize_factor = cur_freq_sum / total_max_freq
        return self._normalize_factor

    @property
    async def cpu_stats(self) -> CPUStatMap:
        """
        通过解析/proc/stat获取每个核心的统计数据

        Returns:
            CPUStatMap: key是核心号，value是CPUStat
        """
        pattern = re.compile(
            r"cpu(\d)\s+([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s"
        )
        cpu_state_info = await self._device.shell("cat /proc/stat")
        matches = pattern.findall(cpu_state_info)

        all_cpu_state = {
            int(group[0]): CPUStat(*map(lambda x: int(x), group[1:]))
            for group in matches
        }
        return all_cpu_state

    @property
    async def cpu_usages(self) -> CPUUsageMap:
        """
        获取每个核心cpu使用率

        获取的是两次采样间隔的cpu使用率，第一获取到的永远是0，你需要再调用一次才能获取到使用率。

        Returns:
            CPUUsageMap: _description_
        """
        normalize_factor = await self.normalize_factor
        cpu_count = await self.count
        cpu_usage = {i: CPUUsage() for i in range(cpu_count)}

        last_cpu_stats = await self.cpu_stats
        await asyncio.sleep(1)
        cpu_stats = await self.cpu_stats
        for index, stat in cpu_stats.items():
            last_cpu_stat = last_cpu_stats[index]
            cpu_diff: CPUStat = stat - last_cpu_stat
            usage = round(cpu_diff.usage, 2)
            normalized = usage * normalize_factor
            cpu_usage[index] = CPUUsage(usage, normalized)
        return cpu_usage

    @property
    async def total_cpu_stat(self) -> CPUStat:
        """
        _summary_

        _extended_summary_

        Returns:
            Optional[CPUStat]: _description_
        """
        pattern = re.compile(
            r"cpu\s+([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s"
        )

        result = await self._device.shell("cat /proc/stat")
        match = pattern.search(result)

        cpu_stat = CPUStat()
        if match is None or len(match.groups()) != 10:
            raise RuntimeError("无法从 /proc/stat 中获取cpu统计")
        else:
            cpu_stat = CPUStat(*map(lambda x: int(x), match.groups()))

        return cpu_stat

    @property
    async def total_cpu_usage(self) -> CPUUsage:
        """
        获取总cpu占用率
         获取的是两次采样间隔的cpu使用率，第一获取到的永远是0，你需要再调用一次才能获取到使用率。

        Args:
            normalized (bool, optional): 标准化占有率. Defaults to False.

        Returns:
            CPUUsage: CPU使用率
        """

        last_total_cpu_stat = await self.total_cpu_stat

        # 用sleep来间隔采样
        # await asyncio.sleep(1)

        total_cpu_stat = await self.total_cpu_stat
        diff = total_cpu_stat - last_total_cpu_stat

        normalize_factor = await self.normalize_factor
        normalized = diff.usage * normalize_factor

        return CPUUsage(diff.usage, normalized)

    @overload
    async def get_pid_cpu_stat(self, pkg_name: str) -> ProcessCPUStat:
        ...

    @overload
    async def get_pid_cpu_stat(self, pid: int) -> ProcessCPUStat:
        ...

    async def get_pid_cpu_stat(self, pid) -> ProcessCPUStat:
        """以pid获取进程cpu状态

        Args:
            pid (int): 进程pid

        Returns:
            ProcessCPUStat: 进程cpu状态
        """
        if isinstance(pid, str):
            try:
                pid = await self._device.get_pid_by_pkgname(pid)
            except:
                return ProcessCPUStat()

        result = await self._device.shell(f"cat /proc/{pid}/stat")

        if "No such file or directory" in result:
            return ProcessCPUStat()
        else:
            items = result.split()
            return ProcessCPUStat(
                items[1],
                int(items[13]),
                int(items[14]),
                int(items[15]),
                int(items[16]),
            )

    @overload
    async def get_pid_cpu_usage(self, pid: int) -> CPUUsage:
        ...

    @overload
    async def get_pid_cpu_usage(self, pid: str) -> CPUUsage:
        ...

    async def get_pid_cpu_usage(self, pid) -> CPUUsage:
        if isinstance(pid, str):
            try:
                pid = await self._device.get_pid_by_pkgname(pid)
            except:
                return CPUUsage()

        normalize_factor = await self.normalize_factor

        last_pid_cpu_stat, last_total_cpu_stat = await asyncio.gather(
            self.get_pid_cpu_stat(pid), self.total_cpu_stat
        )

        pid_stat, total_cpu_stat = await asyncio.gather(
            self.get_pid_cpu_stat(pid), self.total_cpu_stat
        )
        pid_diff = pid_stat - last_pid_cpu_stat
        cpu_diff = total_cpu_stat - last_total_cpu_stat

        app_cpu_usage = pid_diff.total / cpu_diff.total * 100

        normalized = app_cpu_usage * normalize_factor
        return CPUUsage(app_cpu_usage, normalized)

    @property
    async def cpu_name(self) -> str:
        """
        获取CPU名

        Returns:
            str: 名字
        """
        try:
            text: str = await self._device.shell("cat /proc/cpuinfo|grep Hardware")
            name = text.split(":")[1].lstrip()
        except Exception:
            return "Unknow"
        return name

    @property
    async def info(self) -> CPUInfo:
        props = await self._device.properties

        platform = props.get("ro.board.platform", "Unknow")
        cpu_name = await self.cpu_name
        abi = props.get("ro.product.cpu.abi", "Unknow")
        core = await self.count
        freqs = await self.freqs
        freq = freqs[0]

        cpu_info = CPUInfo(platform, cpu_name, abi, core, freq)
        return cpu_info
