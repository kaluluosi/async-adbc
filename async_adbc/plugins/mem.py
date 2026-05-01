import re

from async_adbc.plugin import Plugin, register_plugin
from async_adbc.models import MemInfo, MemStat


@register_plugin("mem", "mem")
class MemPlugin(Plugin):
    async def get_info(self) -> MemInfo:
        """获取内存信息

        单位是 kB

        Returns:
            MemInfo: 内存信息
        """
        mem_total_str = await self._device.shell("cat /proc/meminfo|grep MemTotal")
        swap_total_str = await self._device.shell("cat /proc/meminfo|grep SwapTotal")

        mem_total_match = re.search(r"\d+", mem_total_str)
        swap_total_match = re.search(r"\d+", swap_total_str)

        mem_total = int(mem_total_match.group()) if mem_total_match else 0
        swap_total = int(swap_total_match.group()) if swap_total_match else 0

        return MemInfo(mem_total=mem_total, swap_total=swap_total)

    async def stat(self, package_name: str) -> MemStat:
        """获取应用的内存统计信息

        单位是 kB

        Args:
            package_name: 包名

        Returns:
            MemStat: 内存统计信息
        """
        total_meminfo_re = re.compile(
            r"\s*TOTAL\s+(?P<pss>\d+)\s+(?P<private_dirty>\d+)\s+(?P<private_clean>\d+)\s+(?P<swapped_dirty>\d+)\s+(?P<heap_size>\d+)\s+(?P<heap_alloc>\d+)\s+(?P<heap_free>\d+)"
        )

        cmd = f"dumpsys meminfo {package_name}"
        result = await self._device.shell(cmd)
        match = total_meminfo_re.search(result, 0)

        if match:
            return MemStat(**{k: int(v) for k, v in match.groupdict().items()})
        else:
            return MemStat()
