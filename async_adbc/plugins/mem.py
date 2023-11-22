import re
from pydantic import BaseModel, Field
from async_adbc.plugin import Plugin


class MemInfo(BaseModel):
    mem_total: int  # 内存大小
    swap_total: int  # 交换页大小


class MemStat(BaseModel):
    pss: int = Field(default=0)
    private_dirty: int = Field(default=0)
    private_clean: int = Field(default=0)
    swapped_dirty: int = Field(default=0)
    heap_size: int = Field(default=0)
    heap_alloc: int = Field(default=0)
    heap_free: int = Field(default=0)


class MemPlugin(Plugin):
    @property
    async def info(self) -> MemInfo:
        """
        获取内存信息

        单位是 byte

        Returns:
            MemInfo:
        """

        mem_total_str = await self._device.shell("cat /proc/meminfo|grep MemTotal")
        swap_total_str = await self._device.shell("cat /proc/meminfo|grep SwapTotal")

        mem_total_match = re.search(r"\d+", mem_total_str)
        swap_total_match = re.search(r"\d+", swap_total_str)

        mem_total = mem_total_match.group() if mem_total_match else 0
        swap_total = swap_total_match.group() if swap_total_match else 0

        return MemInfo(mem_total=int(mem_total), swap_total=int(swap_total))

    async def stat(self, package_name: str) -> MemStat:
        """
        获取app的内存性能

        单位是 byte

        _extended_summary_

        Args:
            package_name (str): _description_

        Returns:
            _type_: _description_
        """
        total_meminfo_re = re.compile(
            r"\s*TOTAL\s*(?P<pss>\d+)"
            r"\s*(?P<private_dirty>\d+)"
            r"\s*(?P<private_clean>\d+)"
            r"\s*(?P<swapped_dirty>\d+)"
            r"\s*(?P<heap_size>\d+)"
            r"\s*(?P<heap_alloc>\d+)"
            r"\s*(?P<heap_free>\d+)"
        )

        cmd = f"dumpsys meminfo {package_name}"
        result = await self._device.shell(cmd)
        match = total_meminfo_re.search(result, 0)

        if match:
            return MemStat(**{k: int(v) for k, v in match.groupdict().items()})
        else:
            return MemStat()
