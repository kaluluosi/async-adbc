# BatteryPlugin

电池信息插件，用于获取电池状态。

**访问方式：** `device.battery`

---

## 方法

### stat

```python
async def stat() -> BatteryStat
```

获取电池状态。

**返回：**
- `BatteryStat`: 电池状态对象

**BatteryStat 字段：**
- `ac_powered` (bool): 是否 AC 供电
- `usb_powered` (bool): 是否 USB 供电
- `wireless_powered` (bool): 是否无线供电
- `max_charging_current` (int): 最大充电电流
- `max_charging_voltage` (int): 最大充电电压
- `charge_counter` (int): 充电计数
- `status` (int): 状态
- `health` (int): 健康度
- `present` (bool): 是否存在
- `level` (int): 电量等级
- `scale` (int): 电量最大刻度
- `voltage` (float): 电压
- `temperature` (float): 温度
- `technology` (str): 电池技术

**示例：**
```python
stat = await device.battery.stat()
print(f"电量: {stat.level}/{stat.scale}")
print(f"温度: {stat.temperature}°C")
print(f"电压: {stat.voltage}mV")
print(f"USB 供电: {stat.usb_powered}")
```
