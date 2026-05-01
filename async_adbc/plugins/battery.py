from pydantic import BaseModel, Field
from async_adbc.plugin import Plugin, register_plugin
from async_adbc.models import BatteryStat

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


@register_plugin("battery", "battery")
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
