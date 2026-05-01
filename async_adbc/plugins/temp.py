import re
from typing import List, Optional

from async_adbc.plugin import Plugin, register_plugin
from async_adbc.models import TempStat


@register_plugin("temp", "temp")
class TempPlugin(Plugin):

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

    async def stat(self, check: bool = False) -> TempStat:
        """获取温度统计

        Args:
            check: 是否抛异常

        Returns:
            TempStat: 温度统计
        """
        cpu_temp = 0.0
        gpu_temp = 0.0
        skin_temp = 0.0
        battery_temp = 0.0

        hardware_result = await self._try_shell_commands(["dumpsys hardware_properties"])
        if hardware_result:
            cpu_match = re.search(r"CPU temperatures:\s*\[([0-9.,\s]+)\]", hardware_result)
            if cpu_match:
                cpu_temp = float(cpu_match.group(1).split(",")[0])

            gpu_match = re.search(r"GPU temperatures:\s*\[([0-9.,\s]+)\]", hardware_result)
            if gpu_match:
                gpu_temp = float(gpu_match.group(1).split(",")[0])

            skin_match = re.search(r"Skin temperatures:\s*\[([0-9.,\s]+)\]", hardware_result)
            if skin_match:
                skin_temp = float(skin_match.group(1).split(",")[0])

            battery_match = re.search(r"Battery temperatures:\s*\[([0-9.,\s]+)\]", hardware_result)
            if battery_match:
                battery_temp = float(battery_match.group(1).split(",")[0])

        if cpu_temp == 0:
            thermal_result = await self._try_shell_commands(
                [
                    "cat /sys/class/thermal/thermal_zone0/temp",
                    "cat /sys/class/hwmon/hwmon0/temp1_input",
                ]
            )
            if thermal_result:
                try:
                    cpu_temp = float(thermal_result.strip()) / 1000.0
                except Exception:
                    pass

        if battery_temp == 0:
            battery_result = await self._try_shell_commands(
                ["dumpsys battery | grep 'temperature'"]
            )
            if battery_result:
                match = re.search(r"temperature:\s*(-?\d+)", battery_result)
                if match:
                    battery_temp = float(match.group(1)) / 10.0

        if check and (cpu_temp == 0 and gpu_temp == 0 and skin_temp == 0 and battery_temp == 0):
            raise RuntimeError("无法获取温度信息")

        return TempStat(cpu=cpu_temp, gpu=gpu_temp, skin=skin_temp, battery=battery_temp)
