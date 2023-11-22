import re
from typing import Dict
from collections import defaultdict
from async_adbc.plugin import Plugin


class PropPlugin(Plugin):
    @property
    async def properties(self) -> Dict[str, str]:
        res = await self._device.shell("getprop")
        result_pattern = "^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$"  # type: ignore
        lines = res.splitlines()
        properties = defaultdict(lambda: "")
        for line in lines:
            m = re.match(result_pattern, line)
            if m:
                properties[m.group(1)] = m.group(2)

        return properties

    async def get(self, property_name: str):
        properties = await self.properties
        return properties[property_name]
