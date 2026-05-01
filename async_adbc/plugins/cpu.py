import asyncio
from collections import defaultdict
import re
from typing import Dict, List, Optional, Tuple

from async_lru import alru_cache

from async_adbc.plugin import Plugin, register_plugin
from async_adbc.models import (
    CPUInfo,
    CPUUsage,
    CPUFreq,
    CPUStat,
    ProcessCPUStat,
)


CPUStatMap = Dict[int, CPUStat]
CPUUsageMap = Dict[int, CPUUsage]


@register_plugin("cpu", "cpu")
class CPUPlugin(Plugin):

    @alru_cache
    async def get_count(self) -> int:
        """获取 CPU 核心数

        Returns:
            int: 核心数
        """
        result = await self._device.shell("ls /sys/devices/system/cpu")
        match = re.findall(r"cpu[0-9]+", result)
        return len(match)

    @alru_cache
    async def get_freqs(self) -> List[CPUFreq]:
        """获取所有 CPU 的最小/当前/最大频率

        单位是 Hz

        Returns:
            list[CPUFreq]: CPU 频率列表
        """
        count = await self.get_count()
        try:
            coroutines = []
            for index in range(count):
                cmd_root = f"cat /sys/devices/system/cpu/cpu{index}/cpufreq"
                min_freq = self._device.shell(f"{cmd_root}/cpuinfo_min_freq")
                cur_freq = self._device.shell(f"{cmd_root}/scaling_cur_freq")
                max_freq = self._device.shell(f"{cmd_root}/cpuinfo_max_freq")
                coroutines.append(asyncio.gather(min_freq, cur_freq, max_freq))

            freq_list = await asyncio.gather(*coroutines)
            return [
                CPUFreq(min=int(min_f), cur=int(cur_f), max=int(max_f))
                for min_f, cur_f, max_f in freq_list
            ]
        except Exception:
            return [CPUFreq(min=1, cur=1, max=1) for _ in range(count)]

    @alru_cache
    async def get_normalize_factor(self) -> float:
        """CPU 占用标准化因子

        使用这个因子乘以 CPU 占用率可以得到设备无关的标准化占用率

        Returns:
            float: 标准化因子
        """
        cpu_freqs = await self.get_freqs()
        total_max_freq = sum([f.max for f in cpu_freqs])

        online_cmd = "cat /sys/devices/system/cpu/online"
        online = await self._device.shell(online_cmd)
        phases = [
            list(map(lambda v: int(v), sub))
            for sub in [p.split("-") for p in online.split(",")]
        ]

        cur_freq_sum = 0
        for p in phases:
            for i in range(p[0], p[1] + 1):
                cur_freq_sum += cpu_freqs[i].cur

        return cur_freq_sum / total_max_freq

    async def get_cpu_stats(self) -> CPUStatMap:
        """通过解析 /proc/stat 获取每个核心的统计数据

        Returns:
            CPUStatMap: 核心编号到统计数据的映射
        """
        pattern = re.compile(
            r"cpu(\d)\s+([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s"
        )
        cpu_state_info = await self._device.shell("cat /proc/stat")
        matches = pattern.findall(cpu_state_info)

        values = [list(map(lambda x: int(x), group[1:])) for group in matches]
        all_cpu_state = {
            index: CPUStat(
                user=value[0],
                nice=value[1],
                system=value[2],
                idle=value[3],
                iowait=value[4],
                irq=value[5],
                softirq=value[6],
                stealstolen=value[7],
                guest=value[8],
                guest_nice=value[9],
            )
            for index, value in enumerate(values)
        }
        return all_cpu_state

    async def get_cpu_usages(self) -> CPUUsageMap:
        """获取每个核心 CPU 占用率

        获取的是两次采样间隔的 CPU 占用率，第一次获取到的永远是 0，需要再调用一次才能获取到占用率

        Returns:
            CPUUsageMap: 核心编号到占用率的映射
        """
        normalize_factor = await self.get_normalize_factor()
        cpu_count = await self.get_count()
        cpu_usage = {i: CPUUsage() for i in range(cpu_count)}

        last_cpu_stats = await self.get_cpu_stats()
        await asyncio.sleep(0.1)
        cpu_stats = await self.get_cpu_stats()

        for index, stat in cpu_stats.items():
            last_cpu_stat = last_cpu_stats[index]
            cpu_diff: CPUStat = stat - last_cpu_stat
            usage = round(cpu_diff.usage, 2)
            normalized = usage * normalize_factor
            cpu_usage[index] = CPUUsage(usage=usage, normalized=normalized)
        return cpu_usage

    async def get_total_cpu_stat(self) -> CPUStat:
        """总 CPU 统计数据

        Returns:
            CPUStat: CPU 统计数据
        """
        pattern = re.compile(
            r"cpu\s+([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s"
        )

        result = await self._device.shell("cat /proc/stat")
        match = pattern.search(result)

        cpu_stat = CPUStat()
        if match and len(match.groups()) == 10:
            value = list(map(lambda x: int(x), match.groups()))
            cpu_stat = CPUStat(
                user=value[0],
                nice=value[1],
                system=value[2],
                idle=value[3],
                iowait=value[4],
                irq=value[5],
                softirq=value[6],
                stealstolen=value[7],
                guest=value[8],
                guest_nice=value[9],
            )

        return cpu_stat

    async def get_total_cpu_usage(self) -> CPUUsage:
        """获取总 CPU 占用率

        获取的是两次采样间隔的 CPU 占用率，第一次获取到的永远是 0，需要再调用一次才能获取到占用率

        Returns:
            CPUUsage: CPU 占用率
        """
        last_total_cpu_stat = await self.get_total_cpu_stat()
        await asyncio.sleep(0.1)
        total_cpu_stat = await self.get_total_cpu_stat()
        diff = total_cpu_stat - last_total_cpu_stat

        normalize_factor = await self.get_normalize_factor()
        normalized = diff.usage * normalize_factor

        return CPUUsage(usage=diff.usage, normalized=normalized)

    async def get_pid_cpu_stat(self, pid_or_pkg_name: int | str) -> ProcessCPUStat:
        """通过 PID 或包名获取进程 CPU 统计数据

        Args:
            pid_or_pkg_name: 进程 PID 或包名

        Returns:
            ProcessCPUStat: 进程 CPU 统计数据
        """
        pid = pid_or_pkg_name
        if isinstance(pid_or_pkg_name, str):
            try:
                pid = await self._device.get_pid_by_pkgname(pid_or_pkg_name)
            except Exception:
                return ProcessCPUStat()

        result = await self._device.shell(f"cat /proc/{pid}/stat")
        if "No such file or directory" in result:
            return ProcessCPUStat()
        else:
            items = result.split()
            return ProcessCPUStat(
                name=items[1],
                utime=int(items[13]),
                stime=int(items[14]),
                cutime=int(items[15]),
                cstime=int(items[16]),
            )

    async def get_pid_cpu_usage(self, pid_or_pkg_name: int | str) -> CPUUsage:
        """通过 PID 或包名获取进程 CPU 占用率

        Args:
            pid_or_pkg_name: 进程 PID 或包名

        Returns:
            CPUUsage: CPU 占用率
        """
        pid = pid_or_pkg_name
        if isinstance(pid, str):
            try:
                pid = await self._device.get_pid_by_pkgname(pid_or_pkg_name)
            except Exception:
                return CPUUsage()

        normalize_factor = await self.get_normalize_factor()

        last_pid_cpu_stat, last_total_cpu_stat = await asyncio.gather(
            self.get_pid_cpu_stat(pid), self.get_total_cpu_stat()
        )
        await asyncio.sleep(0.1)
        pid_stat, total_cpu_stat = await asyncio.gather(
            self.get_pid_cpu_stat(pid), self.get_total_cpu_stat()
        )

        pid_diff = pid_stat - last_pid_cpu_stat
        cpu_diff = total_cpu_stat - last_total_cpu_stat

        app_cpu_usage = pid_diff.total / cpu_diff.total * 100
        normalized = app_cpu_usage * normalize_factor
        return CPUUsage(usage=app_cpu_usage, normalized=normalized)

    @alru_cache
    async def get_cpu_name(self) -> str:
        """获取 CPU 名称

        Returns:
            str: CPU 名称
        """
        try:
            text = await self._device.shell("cat /proc/cpuinfo|grep Hardware")
            return text.split(":")[1].lstrip()
        except Exception:
            return "Unknown"

    @alru_cache
    async def get_info(self) -> CPUInfo:
        """获取 CPU 信息

        Returns:
            CPUInfo: CPU 信息
        """
        props = await self._device.get_properties()
        platform = props.get("ro.board.platform", "Unknown")
        cpu_name = await self.get_cpu_name()
        abi = props.get("ro.product.cpu.abi", "Unknown")
        core = await self.get_count()
        freqs = await self.get_freqs()
        freq = freqs[0] if freqs else CPUFreq(min=1, cur=1, max=1)

        return CPUInfo(
            platform=platform,
            name=cpu_name,
            abi=abi,
            core=core,
            freq=(freq.min, freq.max),
        )
