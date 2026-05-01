# MiniCapPlugin

Minicap 截图插件，提供高效的屏幕截图功能。

**访问方式：** `device.minicap`

---

## 方法

### init

```python
async def init()
```

初始化 minicap。将 minicap 可执行文件和库推送到设备。

**示例：**
```python
await device.minicap.init()
```

---

### get_frame

```python
async def get_frame() -> bytes
```

获取当前屏幕帧截图。

**返回：**
- `bytes`: JPEG 格式字节

**抛出：**
- `RuntimeError`: CANNOT LINK EXECUTABLE
- `RuntimeError`: inaccessible or not found

**示例：**
```python
frame = await device.minicap.get_frame()
with open("screenshot.jpg", "wb") as f:
    f.write(frame)
```

---

### screencap

```python
async def screencap(filename: str = "screencap.jpg")
```

截图保存到本地文件。

**参数：**
- `filename` (str): 保存的文件名，默认 "screencap.jpg"

**示例：**
```python
await device.minicap.screencap("myscreenshot.jpg")
```
