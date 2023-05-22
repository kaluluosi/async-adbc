from dataclasses import dataclass
from dataclasses_json import dataclass_json
from . import Plugin


@dataclass_json
@dataclass
class Resolution:
    physical_size: str
    override_size: str


class WMPlugin(Plugin):
    async def size(self):
        res = await self._device.shell("wm", "size")
        lines = res.splitlines()
        p_res = lines[0].split(":")[1].strip()
        o_res = lines[1].split(":")[1].strip()
        return Resolution(p_res, o_res)

    async def orientation(self):
        res = await self._device.shell("dumpsys input|grep SurfaceOrientation")
        v = res.split(":")[1]
        degress = int(v) * 90
        return degress
