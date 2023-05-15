import asyncio
from dataclasses import dataclass

from dataclasses_json import dataclass_json
from . import Plugin


# 如果兼容性实在不行考虑去借鉴solopi
# https://github.com/alipay/SoloPi/blob/ac684afdb1eb654dc27a2710e3c1e5ac25a9c43d/src/shared/src/main/java/com/alipay/hulu/shared/display/items/TemperatureTools.java#L33


@dataclass_json
@dataclass
class TempStat:
    total: int
    cpu: int
    gpu: int
    npu: int
    battery: int


class TempPlugin(Plugin):
    CPU_MARKS = [
        "mtktscpu",  # 联发科
        "tsens_tz_sensor",  # 高通
        "exynos",  # 三星
        "sdm-therm",  # 高通晓龙
        "cpu-0-0-us",  # 通用
        "soc_thermal",  # 通用
        "cpu",  # 通用
    ]
    BATTERY_MARKS = ["battery", "Battery"]
    NPU_MARKS = ["npu-usr", "npu"]
    GPU_MARKS = ["gpuss-0-us", "gpu"]

    SENSOR_LIST_CMD = "cat /sys/devices/virtual/thermal/thermal_zone*/type"
    SENSOR_FILE_LIST_CMD = "cd /sys/devices/virtual/thermal/ && ls|grep thermal_zone"
    SENSOR_TEMP_LIST_CMD = "cat /sys/devices/virtual/thermal/thermal_zone*/temp"
    TEMP_CMD = "cat /sys/devices/virtual/thermal/{filename}/temp"

    @property
    async def sensor_list(self):
        list_str: str = await self._device.shell(self.SENSOR_LIST_CMD)
        return list_str.split("\n")

    @property
    async def sensor_filename_list(self):
        list_str: str = await self._device.shell(self.SENSOR_FILE_LIST_CMD)
        return list_str.split("\n")

    async def get_sensor_temp(self, index: int):
        file_name = self.sensor_list[index]
        temp_value = (
            await self._device.shell(self.TEMP_CMD.format(filename=file_name)) or "0"
        )
        temp_value = self._str_to_temp(temp_value)

        return temp_value

    async def get_senser_index(self, marks):
        sensor_list: list[str] = await self.sensor_list
        for mark in marks:
            for index, sensor_name in enumerate(sensor_list):
                if sensor_name.lower().startswith(mark):
                    return index
        return 0

    def is_temp_valid(self, value):
        return -30 <= value <= 250

    async def get_temp(self):
        total_temp_index = 0
        cpu_temp_index = self.get_senser_index(self.CPU_MARKS)
        gpu_temp_index = self.get_senser_index(self.GPU_MARKS)
        npu_temp_index = self.get_senser_index(self.NPU_MARKS)

        cpu_temp_index, gpu_temp_index, npu_temp_index = asyncio.gather(
            cpu_temp_index, gpu_temp_index, npu_temp_index
        )

        battery_temp_index = await self.get_senser_index(self.BATTERY_MARKS)

        total_temp = 0
        cpu_temp = 0
        gpu_temp = 0
        battery_temp = 0

        if total_temp_index:
            total_temp = await self.get_sensor_temp(total_temp_index)

        if cpu_temp_index:
            cpu_temp = await self.get_sensor_temp(cpu_temp_index)

        if gpu_temp_index:
            gpu_temp = await self.get_sensor_temp(gpu_temp_index)

        if npu_temp_index:
            npu_temp = await self.get_sensor_temp(npu_temp_index)

        if battery_temp_index:
            battery_temp = await self.get_senser_index(battery_temp)

        return TempStat(total_temp, cpu_temp, gpu_temp, npu_temp, battery_temp)

    def _str_to_temp(self, txt: str):
        try:
            temp = float(txt)
            if self.is_temp_valid(temp):
                return temp
            elif self.is_temp_valid(temp / 10):
                return temp / 10
            elif self.is_temp_valid(temp / 1000):
                return temp / 1000
            return 0
        except Exception:
            return -1
