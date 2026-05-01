import asyncio
from collections import defaultdict
import re
from typing import Dict, List, Optional, Tuple, Union

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
    async def _try_shell_commands(self, commands: List[str]) -> Optional[str]:
        """尝试多个命令，返回第一个成功的结果

        Args:
            commands: 命令列表

        Returns:
            str | None: 成功的结果，失败返回 None
        """
        for cmd in commands:
            try:
                result = await self._device.shell(cmd)
                if "No such file" not in result and result.strip():
                    return result
            except Exception:
                continue
        return None

    @alru_cache
    async def get_count(self, check: bool = False) -> int:
        """获取 CPU 核心数

        Args:
            check: 是否抛异常

        Returns:
            int: 核心数
        """
        result = await self._try_shell_commands(["ls /sys/devices/system/cpu"])
        if result:
            match = re.findall(r"cpu[0-9]+", result)
            if match:
                return len(match)

        proc_stat_result = await self._try_shell_commands(["cat /proc/stat"])
        if proc_stat_result:
            matches = re.findall(r"cpu\d+\s+", proc_stat_result)
            if matches:
                return len(matches)

        return 1

    @alru_cache
    async def get_freqs(self, check: bool = False) -> List[CPUFreq]:
        """获取所有 CPU 的最小/当前/最大频率

        单位是 Hz

        Args:
            check: 是否抛异常

        Returns:
            list[CPUFreq]: CPU 频率列表
        """
        count = await self.get_count(check=check)
        try:
            coroutines = []
            for index in range(count):
                cmd_root = f"cat /sys/devices/system/cpu/cpu{index}/cpufreq"
                min_freq = self._try_shell_commands([f"{cmd_root}/cpuinfo_min_freq"])
                cur_freq = self._try_shell_commands([f"{cmd_root}/scaling_cur_freq"])
                max_freq = self._try_shell_commands([f"{cmd_root}/cpuinfo_max_freq"])
                coroutines.append(asyncio.gather(min_freq, cur_freq, max_freq))

            freq_list = await asyncio.gather(*coroutines)
            return [
                CPUFreq(
                    min=int(min_f) if min_f else 1,
                    cur=int(cur_f) if cur_f else 1,
                    max=int(max_f) if max_f else 1,
                )
                for min_f, cur_f, max_f in freq_list
            ]
        except Exception:
            if check:
                raise
            return [CPUFreq(min=1, cur=1, max=1) for _ in range(count)]

    @alru_cache
    async def get_normalize_factor(self, check: bool = False) -> float:
        """CPU 占用标准化因子

        使用这个因子乘以 CPU 占用率可以得到设备无关的标准化占用率

        Args:
            check: 是否抛异常

        Returns:
            float: 标准化因子
        """
        try:
            cpu_freqs = await self.get_freqs(check=check)
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
                    if i < len(cpu_freqs):
                        cur_freq_sum += cpu_freqs[i].cur

            return cur_freq_sum / total_max_freq if total_max_freq > 0 else 1.0
        except Exception:
            if check:
                raise
            return 1.0

    async def get_cpu_stats(self, check: bool = False) -> CPUStatMap:
        """通过解析 /proc/stat 获取每个核心的统计数据

        Args:
            check: 是否抛异常

        Returns:
            CPUStatMap: 核心编号到统计数据的映射
        """
        pattern = re.compile(
            r"cpu(\d)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)"
        )
        cpu_state_info = await self._try_shell_commands(["cat /proc/stat"])

        if cpu_state_info:
            matches = pattern.findall(cpu_state_info)
            values = [list(map(lambda x: int(x), group[1:])) for group in matches]
            return {
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

        if check:
            raise RuntimeError("无法获取 CPU 统计数据")
        return {}

    async def get_cpu_usages(self, check: bool = False) -> CPUUsageMap:
        """获取每个核心 CPU 占用率

        获取的是两次采样间隔的 CPU 占用率，第一次获取到的永远是 0，需要再调用一次才能获取到占用率

        Args:
            check: 是否抛异常

        Returns:
            CPUUsageMap: 核心编号到占用率的映射
        """
        try:
            normalize_factor = await self.get_normalize_factor(check=check)
            cpu_count = await self.get_count(check=check)
            cpu_usage = {i: CPUUsage() for i in range(cpu_count)}

            last_cpu_stats = await self.get_cpu_stats(check=check)
            await asyncio.sleep(0.1)
            cpu_stats = await self.get_cpu_stats(check=check)

            for index, stat in cpu_stats.items():
                if index in last_cpu_stats:
                    last_cpu_stat = last_cpu_stats[index]
                    cpu_diff: CPUStat = stat - last_cpu_stat
                    usage = round(cpu_diff.usage, 2)
                    normalized = usage * normalize_factor
                    cpu_usage[index] = CPUUsage(usage=usage, normalized=normalized)
            return cpu_usage
        except Exception:
            if check:
                raise
            return {}

    async def get_total_cpu_stat(self, check: bool = False) -> CPUStat:
        """总 CPU 统计数据

        Args:
            check: 是否抛异常

        Returns:
            CPUStat: CPU 统计数据
        """
        pattern = re.compile(
            r"cpu\s+([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s([\d]+)\s"
        )

        result = await self._try_shell_commands(["cat /proc/stat"])
        if result:
            match = pattern.search(result)
            if match and len(match.groups()) == 10:
                value = list(map(lambda x: int(x), match.groups()))
                return CPUStat(
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

        if check:
            raise RuntimeError("无法获取 CPU 统计数据")
        return CPUStat()

    async def get_total_cpu_usage(self, check: bool = False) -> CPUUsage:
        """获取总 CPU 占用率

        获取的是两次采样间隔的 CPU 占用率，第一次获取到的永远是 0，需要再调用一次才能获取到占用率

        Args:
            check: 是否抛异常

        Returns:
            CPUUsage: CPU 占用率
        """
        try:
            last_total_cpu_stat = await self.get_total_cpu_stat(check=check)
            await asyncio.sleep(0.1)
            total_cpu_stat = await self.get_total_cpu_stat(check=check)
            diff = total_cpu_stat - last_total_cpu_stat

            normalize_factor = await self.get_normalize_factor(check=check)
            normalized = diff.usage * normalize_factor

            return CPUUsage(usage=diff.usage, normalized=normalized)
        except Exception:
            if check:
                raise
            return CPUUsage()

    async def get_pid_cpu_stat(
        self, pid_or_pkg_name: Union[int, str], check: bool = False
    ) -> ProcessCPUStat:
        """通过 PID 或包名获取进程 CPU 统计数据

        Args:
            pid_or_pkg_name: 进程 PID 或包名
            check: 是否抛异常

        Returns:
            ProcessCPUStat: 进程 CPU 统计数据
        """
        pid = pid_or_pkg_name
        if isinstance(pid_or_pkg_name, str):
            try:
                pid = await self._device.get_pid_by_pkgname(pid_or_pkg_name)
            except Exception:
                if check:
                    raise
                return ProcessCPUStat()

        result = await self._try_shell_commands([f"cat /proc/{pid}/stat"])
        if result and "No such file or directory" not in result:
            items = result.split()
            if len(items) >= 17:
                name = items[1]
                # 去掉括号
                if name.startswith("(") and name.endswith(")"):
                    name = name[1:-1]
                return ProcessCPUStat(
                    name=name,
                    utime=int(items[13]),
                    stime=int(items[14]),
                    cutime=int(items[15]),
                    cstime=int(items[16]),
                )

        if check:
            raise RuntimeError(f"无法获取进程 {pid} 的 CPU 统计数据")
        return ProcessCPUStat()

    async def get_pid_cpu_usage(
        self, pid_or_pkg_name: Union[int, str], check: bool = False
    ) -> CPUUsage:
        """通过 PID 或包名获取进程 CPU 占用率

        Args:
            pid_or_pkg_name: 进程 PID 或包名
            check: 是否抛异常

        Returns:
            CPUUsage: CPU 占用率
        """
        pid = pid_or_pkg_name
        if isinstance(pid, str):
            try:
                pid = await self._device.get_pid_by_pkgname(pid_or_pkg_name)
            except Exception:
                if check:
                    raise
                return CPUUsage()

        try:
            normalize_factor = await self.get_normalize_factor(check=check)

            last_pid_cpu_stat, last_total_cpu_stat = await asyncio.gather(
                self.get_pid_cpu_stat(pid, check=check),
                self.get_total_cpu_stat(check=check),
            )
            await asyncio.sleep(0.1)
            pid_stat, total_cpu_stat = await asyncio.gather(
                self.get_pid_cpu_stat(pid, check=check),
                self.get_total_cpu_stat(check=check),
            )

            pid_diff = pid_stat - last_pid_cpu_stat
            cpu_diff = total_cpu_stat - last_total_cpu_stat

            if cpu_diff.total > 0:
                app_cpu_usage = pid_diff.total / cpu_diff.total * 100
                normalized = app_cpu_usage * normalize_factor
                return CPUUsage(usage=app_cpu_usage, normalized=normalized)

            return CPUUsage()
        except Exception:
            if check:
                raise
            return CPUUsage()

    @alru_cache
    async def get_cpu_name(self, check: bool = False) -> str:
        """获取 CPU 名称

        Args:
            check: 是否抛异常

        Returns:
            str: CPU 名称
        """
        try:
            text = await self._try_shell_commands(["cat /proc/cpuinfo|grep Hardware"])
            if text:
                return text.split(":")[1].lstrip()
            return "Unknown"
        except Exception:
            if check:
                raise
            return "Unknown"

    @alru_cache
    async def get_info(self, check: bool = False) -> CPUInfo:
        """获取 CPU 信息

        Args:
            check: 是否抛异常

        Returns:
            CPUInfo: CPU 信息
        """
        props = await self._device.get_properties()
        platform = props.get("ro.board.platform", "Unknown")
        cpu_name = await self.get_cpu_name(check=check)
        abi = props.get("ro.product.cpu.abi", "Unknown")
        core = await self.get_count(check=check)
        freqs = await self.get_freqs(check=check)
        freq = freqs[0] if freqs else CPUFreq(min=1, cur=1, max=1)

        return CPUInfo(
            platform=platform,
            name=cpu_name,
            abi=abi,
            core=core,
            freq=(freq.min, freq.max),
        )
