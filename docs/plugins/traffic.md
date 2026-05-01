# TrafficPlugin

流量统计插件，用于获取设备和应用的网络流量。

**访问方式：** `device.traffic`

---

## 方法

### global_stat

```python
async def global_stat() -> TrafficStat
```

获取设备的全局网络流量统计信息。

单位是字节（byte）。

**返回：**
- `TrafficStat`: 包含接收和发送字节数的流量统计对象

**TrafficStat 字段：**
- `receive` (float): 接收字节数
- `send` (float): 发送字节数

**TrafficStat 支持的操作：**
- 减法：`stat2 - stat1` 得到差值
- 加法：`stat1 + stat2` 得到总和

**示例：**
```python
# 获取初始流量
stat1 = await device.traffic.global_stat()
print(f"初始 - 接收: {stat1.receive} 字节, 发送: {stat1.send} 字节")

# 等待一段时间
await asyncio.sleep(5)

# 获取后续流量
stat2 = await device.traffic.global_stat()
print(f"后续 - 接收: {stat2.receive} 字节, 发送: {stat2.send} 字节")

# 计算差值
diff = stat2 - stat1
print(f"5秒内 - 接收: {diff.receive} 字节, 发送: {diff.send} 字节")
```

---

### app_stat

```python
async def app_stat(package_name: str) -> TrafficStat
```

获取指定应用的网络流量统计信息。

**参数：**
- `package_name` (str): 应用的包名

**返回：**
- `TrafficStat`: 包含接收和发送字节数的流量统计对象

**抛出：**
- `ValueError`: 如果找不到指定的包名，则抛出该异常

**示例：**
```python
stat = await device.traffic.app_stat("com.example.app")
print(f"应用 - 接收: {stat.receive} 字节, 发送: {stat.send} 字节")
```
