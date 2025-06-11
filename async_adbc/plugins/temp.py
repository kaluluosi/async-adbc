import re
from typing import List
from async_adbc.plugin import Plugin
from pydantic import BaseModel

class TempStat(BaseModel):
    cpu: float
    gpu: float
    skin: float
    battery: float


class TempPlugin(Plugin):
    
    TEMP_PATTERN = r"{name} temperatures:\s*\[([0-9.,\s]+)\]"

    def __init__(self, device) -> None:
        super().__init__(device)


    async def stat(self):
        hardware_properties = await self._device.shell("dumpsys hardware_properties")
        
        # 获取cpu
        cpu_temp = 0
        match = re.search(self.TEMP_PATTERN.format(name="CPU"), hardware_properties)
        if match:
            cpu_temp = float(match.group(1).split(",")[0])

        # 获取gpu
        gpu_temp = 0
        match = re.search(self.TEMP_PATTERN.format(name="GPU"), hardware_properties)
        if match:
            gpu_temp = float(match.group(1).split(",")[0])
            
        # 获取skin
        skin_temp = 0
        match = re.search(self.TEMP_PATTERN.format(name="Skin"), hardware_properties)
        if match:
            skin_temp = float(match.group(1).split(",")[0])

        # 获取battery
        battery_temp = 0
        match = re.search(self.TEMP_PATTERN.format(name="Battery"), hardware_properties)
        if match:
            battery_temp = float(match.group(1).split(",")[0])
            
        return TempStat(cpu=cpu_temp, gpu=gpu_temp, skin=skin_temp, battery=battery_temp)