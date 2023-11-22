from pydantic import BaseModel, Field
from async_adbc.plugin import Plugin

ATTR_MAP = {
        "AC powered": "ac_powered",
        "USB powered": "usb_powered",
        "Wireless powered": "wireless_powered",
        "Max charging current": "max_charging_current",
        "Max charging voltage": "max_charging_voltage",
        "Charge counter": "charge_counter",
        "status": "status",
        "health": "health",
        "present": "present",
        "level": "level",
        "scale": "scale",
        "voltage": "voltage",
        "temperature": "temperature",
        "technology": "technology",
    }  # 属性名字段映射表

class BatteryStat(BaseModel):

    ac_powered: bool = Field(default=False)  # 是否连接AC（电源）充电线
    usb_powered: bool = Field(default=False)  # 是否连接USB（PC或笔记本USB插口）充电
    wireless_powered: bool = Field(default=False)  # 是否使用了无线电源
    max_charging_current: int = Field(default=-1)  # 当前充电电流 mA
    max_charging_voltage: int = Field(default=-1)  # 当前充电电压 mV
    charge_counter: int = Field(default=-1)  # 瞬时电池容量 uA-h
    status: int = Field(default=-1)  # 电池状态，2为充电状态，其他为非充电状态
    health: int = Field(default=-1)  # 池健康状态：只有数字2表示电池良好
    present: bool = Field(default=False)  # 电池是否安装在机身
    level: int = Field(default=-1)  # 电量（%）
    scale: int = Field(default=-1)  # 电量最大数值
    voltage: float = Field(default=-1)  # 当前电压（mV）
    temperature: float = Field(default=-1)  # 电池温度，单位为0.1摄氏度
    technology: str = Field(default="Unknown")  # 电池种类


class BatteryPlugin(Plugin):
    SESSION = "Current Battery Service state:"

    async def stat(self) -> BatteryStat:
        res = await self._device.shell("dumpsys battery")
        lines = res.splitlines()
        try:
            start_line = lines.index(self.SESSION)
        except ValueError:
            start_line = 0

        data = {}
        for line in lines[start_line + 1 :]:
            if not line:
                continue

            attr, value = line.strip().split(":")
            attr = attr.strip()
            value = value.strip()
            if value in ["true", "false"]:
                value = bool(value)
            elif value.isdigit():
                value = int(value)

            attr = ATTR_MAP.get(attr)
            if attr:
                data[attr] = value

        stat = BatteryStat(**data)
        return stat
