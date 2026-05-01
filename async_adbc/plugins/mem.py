import re
from typing import List

from async_adbc.plugin import Plugin, register_plugin
from async_adbc.models import MemInfo, MemStat


@register_plugin("mem", "mem")
class MemPlugin(Plugin):
    async def _try_shell_commands(self, commands: List[str]) -> str | None:
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

    async def get_info(self, check: bool = False) -> MemInfo:
        """获取内存信息

        单位是 kB

        Args:
            check: 是否抛异常

        Returns:
            MemInfo: 内存信息
        """
        mem_total = 0
        swap_total = 0

        meminfo_result = await self._try_shell_commands(["cat /proc/meminfo"])
        if meminfo_result:
            mem_total_match = re.search(r"MemTotal:\s*(\d+)", meminfo_result)
            swap_total_match = re.search(r"SwapTotal:\s*(\d+)", meminfo_result)
            mem_total = int(mem_total_match.group()) if mem_total_match else 0
            swap_total = int(swap_total_match.group()) if swap_total_match else 0

        return MemInfo(mem_total=mem_total, swap_total=swap_total)

    async def stat(self, package_name: str, check: bool = False) -> MemStat:
        """获取应用的内存统计信息

        单位是 kB

        Args:
            package_name: 包名
            check: 是否抛异常

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
