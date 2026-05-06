# ScrcpyPlugin

Scrcpy 插件，提供屏幕截图和视频录制功能。基于 Scrcpy 项目 v3.3.4。

**访问方式：** `device.scrcpy`

---

## 安装可选依赖

使用 Scrcpy 插件的图片解码功能需要安装可选依赖：

```bash
pip install async-adbc[scrcpy]
# 或单独安装
pip install av pillow
```

---

## 简介

Scrcpy 插件集成了 Scrcpy 功能，可以：
- 获取设备屏幕截图（PNG/JPG）
- 获取设备屏幕的 H.264 视频流
- 录制视频到本地文件

---

## 快速开始

```python
import asyncio
from async_adbc import ADBClient

async def main():
    adbc = ADBClient()
    device = await adbc.device()

    # 启动 scrcpy
    await device.scrcpy.start(max_fps=15)

    # 获取一帧截图并保存为 png
    h264_data = await device.scrcpy.screencap(save_file="screenshot.png")
    print(f"截图完成，原始数据: {len(h264_data)} 字节")

    # 停止 scrcpy
    await device.scrcpy.stop()

asyncio.run(main())
```

---

## 方法

### start

```python
async def start(max_size: int = 0, max_fps: int = 0, bit_rate: int = 8000000, stay_awake: bool = True)
```

启动 scrcpy 服务器并建立连接。

**参数：**
- `max_size` (int): 最大分辨率，0 表示不限制
- `max_fps` (int): 最大帧率，0 表示不限制
- `bit_rate` (int): 比特率，默认 8000000 (8Mbps)
- `stay_awake` (bool): 是否保持设备常亮，默认 True

**示例：**
```python
# 使用默认配置启动
await device.scrcpy.start()

# 限制最大分辨率为 720p，帧率 15fps
await device.scrcpy.start(max_size=720, max_fps=15)
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

### screencap

```python
async def screencap(save_file: Optional[str] = None, timeout: float = 3.0) -> bytes
```

获取一帧截图并返回原始 H.264 数据。

如果指定 `save_file`，则会自动保存文件：
- `.png/.jpg/.jpeg`：自动解码并保存为图片
- `.h264`：保存原始 H.264 数据
- 无扩展名：默认保存为 PNG

**参数：**
- `save_file` (str | None): 保存文件路径
- `timeout` (float): 超时时间，默认 3.0

**返回：**
- `bytes`: 原始 H.264 二进制数据

**示例：**
```python
# 直接返回数据，不保存
h264_data = await device.scrcpy.screencap()

# 保存为 PNG
await device.scrcpy.screencap("screenshot.png")

# 保存为 JPG
await device.scrcpy.screencap("screenshot.jpg")

# 保存原始 H.264
await device.scrcpy.screencap("screenshot.h264")
```

---

### stream_frames

```python
async def stream_frames() -> AsyncGenerator[bytes, None]
```

异步生成器，流式获取 H.264 视频帧数据。

**示例：**
```python
async for chunk in device.scrcpy.stream_frames():
    # 处理数据...
    if should_stop:
        break
```

---

### record

```python
async def record(output_path: str, duration: float = 10.0)
```

录制视频到本地文件（保存原始 H.264 数据）。

**参数：**
- `output_path` (str): 输出文件路径
- `duration` (float): 录制时长（秒），默认 10.0

**示例：**
```python
await device.scrcpy.record("video.h264", duration=10.0)
```

---

### device_info (属性)

获取设备信息（包含名称和分辨率）。

**示例：**
```python
await device.scrcpy.start()
info = device.scrcpy.device_info
print(f"设备名: {info.name}, 分辨率: {info.width}x{info.height}")
```

---

## Async with 上下文管理器

支持 `async with` 自动管理 start/stop：

```python
async with device.scrcpy:
    await device.scrcpy.screencap("test.png")
# 退出块时自动调用 stop()
```

---

## 完整示例

### 连续截图

```python
import asyncio
from async_adbc import ADBClient

async def multi_screenshot():
    adbc = ADBClient()
    device = await adbc.device()

    await device.scrcpy.start(max_fps=15)

    for i in range(5):
        await device.scrcpy.screencap(f"frame_{i}.png")
        await asyncio.sleep(0.5)

    await device.scrcpy.stop()

asyncio.run(multi_screenshot())
```

### 录制视频

```python
import asyncio
from pathlib import Path
from async_adbc import ADBClient

async def record_video():
    adbc = ADBClient()
    device = await adbc.device()

    await device.scrcpy.start(max_fps=15, max_size=720)

    # 录制 10 秒
    await device.scrcpy.record("output.h264", duration=10.0)

    await device.scrcpy.stop()

    print(f"视频已保存到 output.h264")

asyncio.run(record_video())
```

---

## 注意事项

1. 确保设备已启用 USB 调试
2. `start()` 和 `stop()` 需要配对使用
3. 使用 `max_size` 可以降低分辨率，提高性能
4. 使用完毕后务必调用 `stop()` 清理资源
5. 图片解码功能需要安装可选依赖 `av` 和 `pillow`
