import os
import re

from . import Plugin


class PropPlugin(Plugin):
    @property
    async def properties(self) -> dict[str, str]:
        res = await self._device.shell("getprop")
        result_pattern = "^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$"  # type: ignore
        lines = res.splitlines()
        properties = {}
        for line in lines:
            m = re.match(result_pattern, line)
            if m:
                properties[m.group(1)] = m.group(2)

        return properties
