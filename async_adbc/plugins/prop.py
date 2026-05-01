import re
from typing import Dict
from collections import defaultdict

from async_lru import alru_cache

from async_adbc.plugin import Plugin, register_plugin


@register_plugin("prop", "prop")
class PropPlugin(Plugin):
    @alru_cache
    async def get_properties(self) -> Dict[str, str]:
        """获取所有属性

        Returns:
            dict[str, str]: 属性字典
        """
        res = await self._device.shell("getprop")
        result_pattern = r"^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$"
        lines = res.splitlines()
        properties = defaultdict(lambda: "")
        for line in lines:
            m = re.match(result_pattern, line)
            if m:
                properties[m.group(1)] = m.group(2)

        return properties

    async def get(self, property_name: str) -> str:
        """获取属性

        Args:
            property_name: 属性名

        Returns:
            str: 属性值
        """
        properties = await self.get_properties()
        return properties[property_name]
