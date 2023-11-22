from pydantic import BaseModel
from async_adbc.plugin import Plugin


class Resolution(BaseModel):
    physical_size: str
    override_size: str


class WMPlugin(Plugin):
    async def size(self):
        res = await self._device.shell("wm", "size")
        lines = res.splitlines()
        p_res = lines[0].split(":")[1].strip()
        if len(lines) > 1:
            o_res = lines[1].split(":")[1].strip()
        else:
            o_res = "?x?"
        return Resolution(physical_size=p_res, override_size=o_res)

    async def orientation(self):
        """
        获取当前旋转角度

        Raises:
            ValueError: 旋转角度无法获取

        Returns:
            _type_: _description_
        """
        res = await self._device.shell("dumpsys input|grep SurfaceOrientation")
        lines = res.splitlines()
        if len(lines) == 0:
            raise RuntimeError("无法获得旋转角度", res)

        v = lines[0].split(":")[1].strip()
        degress = int(v) * 90
        return degress
