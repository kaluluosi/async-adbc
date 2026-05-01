# FpsPlugin

帧率统计插件，用于获取应用的帧率信息。

**访问方式：** `device.fps`

---

## 方法

### stat

```python
async def stat(package_name: str) -> FpsStat
```

获取应用的帧率统计。

**参数：**
- `package_name` (str): 包名

**返回：**
- `FpsStat`: 帧率数据

**FpsStat 字段：**
- `fps` (float): 帧率
- `jank` (float): 卡顿次数
- `big_jank` (float): 严重卡顿次数
- `frametimes` (List[float]): 帧时间列表（毫秒）

**示例：**
```python
stat = await device.fps.stat("com.example.app")
print(f"FPS: {stat.fps:.2f}")
print(f"Jank: {stat.jank}")
print(f"Big Jank: {stat.big_jank}")
print(f"Frame times: {stat.frametimes}")
```

---

### get_surface_view

```python
async def get_surface_view(package_name: str) -> Optional[str]
```

获取应用的 Surface View。

**参数：**
- `package_name` (str): 包名

**返回：**
- `Optional[str]`: Surface View 名称，找不到返回 None

**示例：**
```python
surface = await device.fps.get_surface_view("com.example.app")
if surface:
    print(f"Surface: {surface}")
```
