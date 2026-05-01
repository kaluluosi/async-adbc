# ScrcpyPlugin

Scrcpy 插件，提供屏幕镜像和设备控制功能。基于 Scrcpy 项目，支持获取 H.264 视频流、模拟点击、滑动、按键等操作。

**访问方式：** `device.scrcpy`

---

## 简介

Scrcpy 插件集成了 Scrcpy 功能，可以：
- 获取设备屏幕的 H.264 视频流
- 模拟触摸输入（点击、滑动）
- 发送按键事件
- 输入文本
- 实时屏幕镜像

---

## 快速开始

```python
import asyncio
from async_adbc import ADBClient

async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 启动 scrcpy
    await device.scrcpy.start(max_size=1080, bit_rate=4000000)
    
    # 获取一帧画面
    frame = await device.scrcpy.get_frame()
    if frame:
        print(f"获取到视频帧，大小: {len(frame)} 字节")
    
    # 模拟点击
    await device.scrcpy.tap(500, 500)
    
    # 模拟滑动
    await device.scrcpy.swipe(100, 1000, 100, 200, duration=0.5)
    
    # 输入文本
    await device.scrcpy.text("Hello async-adbc!")
    
    # 停止 scrcpy
    await device.scrcpy.stop()

asyncio.run(main())
```

---

## 方法

### init

```python
async def init()
```

初始化 scrcpy，推送 scrcpy-server.jar 到设备。通常不需要手动调用，`start()` 方法会自动调用。

**示例：**
```python
await device.scrcpy.init()
```

---

### start

```python
async def start(max_size: int = 0, bit_rate: int = 8000000, port: Optional[int] = None)
```

启动 scrcpy 服务器并建立连接。

**参数：**
- `max_size` (int): 最大分辨率，0 表示不限制
- `bit_rate` (int): 比特率，默认 8000000 (8Mbps)
- `port` (Optional[int]): 本地端口，None 则使用默认端口 27183

**示例：**
```python
# 使用默认配置启动
await device.scrcpy.start()

# 限制最大分辨率为 1080p，比特率为 4Mbps
await device.scrcpy.start(max_size=1080, bit_rate=4000000)

# 使用自定义端口
await device.scrcpy.start(port=27184)
```

---

### stop

```python
async def stop()
```

停止 scrcpy 服务器并清理资源。

**示例：**
```python
await device.scrcpy.stop()
```

---

### get_frame

```python
async def get_frame() -> Optional[bytes]
```

获取当前视频帧。

**返回：**
- `Optional[bytes]`: 视频帧数据（H.264 编码），如果没有数据则返回 None

**示例：**
```python
frame = await device.scrcpy.get_frame()
if frame:
    print(f"帧大小: {len(frame)} 字节")
    # 可以保存到文件或进行解码处理
    with open("frame.h264", "wb") as f:
        f.write(frame)
```

---

### tap

```python
async def tap(x: int, y: int)
```

模拟点击。

**参数：**
- `x` (int): x 坐标
- `y` (int): y 坐标

**示例：**
```python
# 点击屏幕中心
await device.scrcpy.tap(540, 960)
```

---

### swipe

```python
async def swipe(x1: int, y1: int, x2: int, y2: int, duration: float = 0.3)
```

模拟滑动。

**参数：**
- `x1, y1` (int): 起始坐标
- `x2, y2` (int): 结束坐标
- `duration` (float): 持续时间（秒），默认 0.3

**示例：**
```python
# 从下往上滑动（类似滚动）
await device.scrcpy.swipe(500, 1500, 500, 500, duration=0.5)
```

---

### keycode

```python
async def keycode(keycode: int)
```

发送按键事件。

**参数：**
- `keycode` (int): Android 键码

**常用键码：**
- `3`: HOME 键
- `4`: 返回键
- `26`: 电源键
- `24`: 音量加
- `25`: 音量减

**示例：**
```python
from async_adbc import Keycode

# 按下 HOME 键
await device.scrcpy.keycode(Keycode.KEYCODE_HOME)

# 按下返回键
await device.scrcpy.keycode(Keycode.KEYCODE_BACK)
```

---

### text

```python
async def text(text: str)
```

输入文本。

**参数：**
- `text` (str): 要输入的文本

**示例：**
```python
await device.scrcpy.text("Hello, World!")
```

---

## StreamReceiver 类

用于接收视频流的类，通常通过 `get_frame()` 获取帧数据，或设置回调实时处理。

### set_frame_callback

```python
def set_frame_callback(callback: Callable[[bytes], None])
```

设置帧数据回调函数。

**参数：**
- `callback` (Callable[[bytes], None]): 回调函数，接收帧数据作为参数

**示例：**
```python
def on_frame(frame_data):
    print(f"收到新帧，大小: {len(frame_data)}")

# 设置回调
device.scrcpy._stream_receiver.set_frame_callback(on_frame)
```

---

## 完整示例

### 实时屏幕录制

```python
import asyncio
from async_adbc import ADBClient

async def record_screen():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 启动 scrcpy
    await device.scrcpy.start(max_size=720, bit_rate=2000000)
    
    # 录制 10 秒
    frames = []
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < 10:
        frame = await device.scrcpy.get_frame()
        if frame:
            frames.append(frame)
        await asyncio.sleep(0.01)
    
    # 保存所有帧
    with open("screen_recording.h264", "wb") as f:
        for frame in frames:
            f.write(frame)
    
    print(f"录制完成，共 {len(frames)} 帧")
    
    # 停止 scrcpy
    await device.scrcpy.stop()

asyncio.run(record_screen())
```

### 自动化操作

```python
import asyncio
from async_adbc import ADBClient, Keycode

async def automate():
    adbc = ADBClient()
    device = await adbc.device()
    
    await device.scrcpy.start()
    
    # 按下 HOME 键
    await device.scrcpy.keycode(Keycode.KEYCODE_HOME)
    await asyncio.sleep(1)
    
    # 点击应用图标（假设位置）
    await device.scrcpy.tap(200, 300)
    await asyncio.sleep(2)
    
    # 输入文本
    await device.scrcpy.text("test input")
    await asyncio.sleep(1)
    
    # 返回
    await device.scrcpy.keycode(Keycode.KEYCODE_BACK)
    
    await device.scrcpy.stop()

asyncio.run(automate())
```

---

## 注意事项

1. 确保设备已启用 USB 调试
2. `start()` 和 `stop()` 需要配对使用
3. 获取帧时第一次可能返回 None，需要稍等片刻
4. 坐标基于设备屏幕原始分辨率
5. 使用完毕后务必调用 `stop()` 清理资源，否则可能导致端口占用
