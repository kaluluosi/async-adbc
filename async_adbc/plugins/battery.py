from dataclasses import dataclass, field

from dataclasses_json import dataclass_json
from . import Plugin


@dataclass_json
@dataclass
class BatteryStat:
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

    ac_powered: bool = field(default=False)  # 是否连接AC（电源）充电线
    usb_powered: bool = field(default=False)  # 是否连接USB（PC或笔记本USB插口）充电
    wireless_powered: bool = field(default=False)  # 是否使用了无线电源
    max_charging_current: int = field(default=-1)  # 当前充电电流 mA
    max_charging_voltage: int = field(default=-1)  # 当前充电电压 mV
    charge_counter: int = field(default=-1)  # 瞬时电池容量 uA-h
    status: int = field(default=-1)  # 电池状态，2为充电状态，其他为非充电状态
    health: int = field(default=-1)  # 池健康状态：只有数字2表示电池良好
    present: bool = field(default=False)  # 电池是否安装在机身
    level: int = field(default=-1)  # 电量（%）
    scale: int = field(default=-1)  # 电量最大数值
    voltage: float = field(default=-1)  # 当前电压（mV）
    temperature: float = field(default=-1)  # 电池温度，单位为0.1摄氏度
    technology: str = field(default="Unknown")  # 电池种类


class BatteryPlugin(Plugin):
    SESSION = "Current Battery Service state:"

    async def stat(self) -> BatteryStat:
        res = await self._device.shell("dumpsys battery")
        lines = res.splitlines()
        start_line = lines.index(self.SESSION)

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

            attr = BatteryStat.ATTR_MAP.get(attr)
            if attr:
                data[attr] = value

        stat = BatteryStat(**data)
        return stat
