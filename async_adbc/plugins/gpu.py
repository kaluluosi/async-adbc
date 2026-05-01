from async_adbc.plugin import Plugin, register_plugin
from async_adbc.models import GPUInfo


@register_plugin("gpu", "gpu")
class GPUPlugin(Plugin):
    @property
    async def info(self) -> GPUInfo:
        text: str = await self._device.shell("dumpsys SurfaceFlinger |grep GLES")
        text = text.split(":")[1]
        manufactor, name, opengl = text.split(",")[:3]
        manufactor = manufactor.strip()
        name = name.strip()
        opengl = opengl.strip()
        return GPUInfo(manufactor=manufactor, name=name, opengl=opengl)
