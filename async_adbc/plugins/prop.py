import re
from typing import Dict, List
from collections import defaultdict

from async_lru import alru_cache

from async_adbc.plugin import Plugin, register_plugin


@register_plugin("prop", "prop")
class PropPlugin(Plugin):
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

    @alru_cache
    async def get_properties(self, check: bool = False) -> Dict[str, str]:
        """获取所有属性

        Args:
            check: 是否抛异常

        Returns:
            dict[str, str]: 属性字典
        """
        res = await self._try_shell_commands(["getprop"])
        if res:
            result_pattern = r"^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$"
            lines = res.splitlines()
            properties = defaultdict(lambda: "")
            for line in lines:
                m = re.match(result_pattern, line)
                if m:
                    properties[m.group(1)] = m.group(2)
            return dict(properties)

        if check:
            raise RuntimeError("无法获取属性信息")
        return {}

    async def get(self, property_name: str, check: bool = False) -> str:
        """获取属性

        Args:
            property_name: 属性名
            check: 是否抛异常

        Returns:
            str: 属性值
        """
        properties = await self.get_properties(check=check)
        value = properties.get(property_name, "")

        if check and not value:
            raise KeyError(f"属性 {property_name} 不存在")
        return value
