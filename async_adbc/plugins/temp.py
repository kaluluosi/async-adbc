import asyncio
from typing import List
from async_adbc.plugin import Plugin
from pydantic import BaseModel
from async_lru import alru_cache


# XXX: 如果兼容性实在不行考虑去借鉴solopi
# https://github.com/alipay/SoloPi/blob/ac684afdb1eb654dc27a2710e3c1e5ac25a9c43d/src/shared/src/main/java/com/alipay/hulu/shared/display/items/TemperatureTools.java#L33


class TempStat(BaseModel):
    cpu: float
    gpu: float
    npu: float
    battery: float


class TempPlugin(Plugin):
    CPU_MARKS = [
        "cpu-0-0",  # 通用
        "cpu-0-0-us",  # 通用
        "mtktscpu",  # 联发科
        "tsens_tz_sensor",  # 高通
        "exynos",  # 三星
        "sdm-therm",  # 高通晓龙
        "soc_thermal",  # 通用
        "cpu",  # 通用
    ]
    BATTERY_MARKS = ["battery", "Battery"]
    NPU_MARKS = ["npu-usr", "npu"]
    GPU_MARKS = ["gpuss-0-us", "gpu"]

    SENSOR_LIST_CMD = "cat /sys/devices/virtual/thermal/thermal_zone*/type"
    SENSOR_FILE_LIST_CMD = "cd /sys/devices/virtual/thermal/ && ls|grep thermal_zone"
    SENSOR_TEMP_LIST_CMD = "cat /sys/devices/virtual/thermal/thermal_zone*/temp"
    TEMP_CMD = "/sys/devices/virtual/thermal/{filename}/temp"

    # 回滚保底温度记录文件
    PLAY_BACK_TEMP_FILE_LIST = [
        "/sys/devices/system/cpu/cpu0/cpufreq/cpu_temp",
        "/sys/devices/system/cpu/cpu0/cpufreq/FakeShmoo_cpu_temp",
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/thermal/thermal_zone1/temp",
        "/sys/class/i2c-adapter/i2c-4/4-004c/temperature",
        "/sys/devices/platform/tegra-i2c.3/i2c-4/4-004c/temperature",
        "/sys/devices/platform/omap/omap_temp_sensor.0/temperature",
        "/sys/devices/platform/tegra_tmon/temp1_input",
        "/sys/kernel/debug/tegra_thermal/temp_tj",
        "/sys/devices/platform/s5p-tmu/temperature",
        "/sys/devices/virtual/thermal/thermal_zone0/temp",
        "/sys/class/hwmon/hwmon0/device/temp1_input",
        "/sys/devices/virtual/thermal/thermal_zone1/temp",
        "/sys/devices/platform/s5p-tmu/curr_temp",
    ]

    def __init__(self, device) -> None:
        super().__init__(device)
        self._thermal_map = None
        self._playback_cpu_temp_file = None

    @alru_cache
    async def _get_thermal_map(self):
        sensor_list = await self._device.shell(self.SENSOR_LIST_CMD)
        sensor_list = sensor_list.splitlines()

        sensor_file_list = await self._device.shell(self.SENSOR_FILE_LIST_CMD)
        sensor_file_list = sensor_file_list.splitlines()

        file_type_map = [
            (self.TEMP_CMD.format(filename=sensor_file_list[i]), v)
            for i, v in enumerate(sensor_list)
        ]
        return file_type_map

    async def _get_temp_file(self, marks: List[str]):
        _thermal_map = await self._get_thermal_map()

        for mark in marks:
            for thermal in _thermal_map:
                if mark in thermal[1]:
                    return thermal[0]

        return await self._get_playback_cpu_temp_file()

    @alru_cache
    async def _get_playback_cpu_temp_file(self):
        """保底的CPU温度方案，当传感器都读不到温度的时候默认用Solopi同款 CPU温度"""

        for temp_file in self.PLAY_BACK_TEMP_FILE_LIST:
            res = await self._device.shell("cat", temp_file)
            res = res.strip()
            if res.isdigit():
                int(res)
                _playback_cpu_temp_file = temp_file
                return _playback_cpu_temp_file
        raise FileNotFoundError("没有合适的温度文件读取")

    async def _get_temp(self, marks: List[str]):
        try:
            temp_file = await self._get_temp_file(marks)
            content = await self._device.shell("cat", temp_file)
            return self._str_to_temp(content)
        except FileNotFoundError:
            return 0

    def _is_temp_valid(self, value):
        return -30 <= value <= 250

    async def stat(self):
        cpu_temp = self._get_temp(self.CPU_MARKS)
        gpu_temp = self._get_temp(self.GPU_MARKS)
        npu_temp = self._get_temp(self.NPU_MARKS)
        battery_temp = self._get_temp(self.BATTERY_MARKS)

        cpu_temp, gpu_temp, npu_temp, battery_temp = await asyncio.gather(
            cpu_temp, gpu_temp, npu_temp, battery_temp
        )

        return TempStat(
            cpu=cpu_temp,
            gpu=gpu_temp,
            npu=npu_temp,
            battery=battery_temp,
        )

    def _str_to_temp(self, txt: str):
        """字符串数值转摄氏度

        Args:
            txt (str): _description_

        Returns:
            _type_: _description_
        """
        try:
            temp = float(txt)
            if self._is_temp_valid(temp):
                return temp
            elif self._is_temp_valid(temp / 10):
                return temp / 10
            elif self._is_temp_valid(temp / 1000):
                return temp / 1000
            return 0
        except Exception:
            return -1
