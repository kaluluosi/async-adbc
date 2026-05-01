# TempPlugin

温度插件，用于获取设备各部件的温度。

**访问方式：** `device.temp`

---

## 方法

### stat

```python
async def stat(check: bool = False) -> TempStat
```

获取温度统计。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `TempStat`: 温度统计

**TempStat 字段：**
- `cpu` (float): CPU 温度（°C）
- `gpu` (float): GPU 温度（°C）
- `skin` (float): 外壳温度（°C）
- `battery` (float): 电池温度（°C）

**示例：**
```python
temp = await device.temp.stat()
print(f"CPU 温度: {temp.cpu:.1f}°C")
print(f"GPU 温度: {temp.gpu:.1f}°C")
print(f"电池温度: {temp.battery:.1f}°C")
```
