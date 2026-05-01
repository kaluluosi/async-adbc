# WMPlugin (Window Manager)

窗口管理插件，用于获取屏幕分辨率和方向。

**访问方式：** `device.wm`

---

## 方法

### size

```python
async def size() -> Resolution
```

获取屏幕分辨率。

**返回：**
- `Resolution`: 分辨率对象

**Resolution 字段：**
- `physical_size` (str): 物理分辨率，格式 "WxH"
- `override_size` (str): 覆盖分辨率

**示例：**
```python
res = await device.wm.size()
print(f"物理分辨率: {res.physical_size}")
print(f"覆盖分辨率: {res.override_size}")
```

---

### orientation

```python
async def orientation() -> int
```

获取当前旋转角度。

**返回：**
- `int`: 旋转角度（0, 90, 180, 270）

**抛出：**
- `RuntimeError`: 旋转角度无法获取

**示例：**
```python
angle = await device.wm.orientation()
print(f"旋转角度: {angle}°")
```
