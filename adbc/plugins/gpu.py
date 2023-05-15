from dataclasses import dataclass
from dataclasses_json import dataclass_json
from . import Plugin


@dataclass
@dataclass_json
class GPUInfo:
    manufactor: str
    name: str
    opengl: str


class GPUPlugin(Plugin):
    async def info(self) -> GPUInfo:
        text: str = await self._device.shell("dumpsys SurfaceFlinger |grep GLES")
        text = text.split(":")[1]
        manufactor, name, opengl = text.split(",")[:3]
        return {
            "manufactor": manufactor.strip(),
            "name": name.strip(),
            "opengl": opengl.strip(),
        }
