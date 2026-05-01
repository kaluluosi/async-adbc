from typing import List, Optional

from async_adbc.plugin import Plugin, register_plugin
from async_adbc.models import GPUInfo


@register_plugin("gpu", "gpu")
class GPUPlugin(Plugin):
    async def _try_shell_commands(self, commands: List[str]) -> Optional[str]:
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

    async def get_info(self, check: bool = False) -> GPUInfo:
        """获取 GPU 信息

        Args:
            check: 是否抛异常

        Returns:
            GPUInfo: GPU 信息
        """
        text = await self._try_shell_commands(["dumpsys SurfaceFlinger |grep GLES"])
        if text and ":" in text:
            try:
                text = text.split(":")[1]
                parts = text.split(",")
                manufactor = parts[0].strip() if len(parts) > 0 else "Unknown"
                name = parts[1].strip() if len(parts) > 1 else "Unknown"
                opengl = parts[2].strip() if len(parts) > 2 else "Unknown"
                return GPUInfo(manufactor=manufactor, name=name, opengl=opengl)
            except Exception:
                pass

        if check:
            raise RuntimeError("无法获取 GPU 信息")
        return GPUInfo(manufactor="Unknown", name="Unknown", opengl="Unknown")
