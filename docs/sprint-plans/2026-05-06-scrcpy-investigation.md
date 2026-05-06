# Scrcpy 插件可行性研究 - 2026-05-06

## 摘要
成功验证 **scrcpy-server v3.3.4** 在 **Android 9 (API 28) x86_64 模拟器**上是完全可行的！成功连接并获取到 H.264 视频流，解码出 720x408 截图！

---

## 最终验证结果 ✅ (2026-05-06)

### 使用 async-adbc 完整流程验证成功！

| 验证项 | 状态 |
|--------|------|
| async-adbc 的 reverse API | ✅ 正常工作 |
| async-adbc 的 shell_reader API | ✅ 正常工作（启动持续运行的 server） |
| 建立 socket 连接 | ✅ 成功 |
| 握手协议 | ✅ 成功 |
| 接收 H.264 视频流 | ✅ 成功，收到 **77,681 字节** |

### 关键文件
- `test_demo.py` - 使用纯 adb 命令行的预演（已验证可行）
- `test_async_adbc_scrcpy.py` - 使用 async-adbc API 的完整验证（已验证可行）
- `async_adbc_scrcpy.h264` - 使用 async-adbc 收到的视频流数据
- `scrcpy_stream.h264` - 使用纯 adb 命令收到的视频流数据

---

## 测试环境

| 项 | 值 |
|----|-----|
| 设备 | 127.0.0.1:5555 (模拟器) |
| Android 版本 | 9 (API 28) |
| 架构 | x86_64 |
| 型号 | SM-S908E |
| scrcpy-server 版本 | 3.3.4 |

## 最终验证 - 完整步骤

### 1. 前置准备
```bash
# 需要的工具
- adb
- Python 3.8+
- PyAV (用于解码 H.264)
- Pillow (用于保存图片)
```

### 2. 关键步骤

#### a) 先在 PC 端监听端口
```python
import socket
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(("127.0.0.1", 27183))
server_sock.listen(1)
```

#### b) 设置 adb reverse
```bash
adb reverse localabstract:scrcpy tcp:27183
```

#### c) 推送并启动 scrcpy-server
```bash
adb push scrcpy-server-v3.3.4 /data/local/tmp/scrcpy-server

adb shell "CLASSPATH=/data/local/tmp/scrcpy-server app_process / com.genymobile.scrcpy.Server 3.3.4 log_level=debug max_size=720 max_fps=15 stay_awake=true"
```

#### d) Accept 连接
```python
client_sock, addr = server_sock.accept()
```

#### e) 握手协议
```python
# 1. 接收 dummy byte (1 byte)
dummy = sock.recv(1)

# 2. 接收设备名称 (64 bytes, null-terminated)
device_name = sock.recv(64).split(b'\x00')[0].decode()

# 3. 接收宽度 (4 bytes, big-endian)
width = int.from_bytes(sock.recv(4), 'big')

# 4. 接收高度 (4 bytes, big-endian)
height = int.from_bytes(sock.recv(4), 'big')
```

#### f) 接收 H.264 流
```python
# 之后收到的就是 H.264 视频流数据
# 可以保存到文件，或者直接用 PyAV 解码
data = sock.recv(8192)
```

### 3. 解码 H.264 流
用 PyAV 解码并提取截图：
```python
import av

container = av.open("scrcpy_stream.h264")
for frame in container.decode(video=0):
    img = frame.to_image()  # PIL Image
    img.save(f"frame_{count:04d}.png")
    break
```

---

## 踩过的坑（必看！）

### 坑 #1：scrcpy-server 文件是假的！
**问题**：
- 之前的 `async_adbc/vendor/scrcpy/scrcpy-server-v3.3.4.jar` 只有 **76 字节**！
- 根本不是有效的 JAR/Dex 文件！
- 内容是："Couldn't find the requested file /server/scrcpy-server in Genymobile/scrcpy"

**解决方案**：
- 从 GitHub Releases 重新下载真正的 server：
  ```
  https://github.com/Genymobile/scrcpy/releases/download/v3.3.4/scrcpy-server-v3.3.4
  ```
- 真正的文件大小：**90,980 字节 (~90KB)**

---

### 坑 #2：参数格式完全搞错了！
**scrcpy v3.3.4 的正确启动格式**：
```bash
app_process / com.genymobile.scrcpy.Server <version> <key1>=<value1> <key2>=<value2> ...
```

**错误格式 #1**（位置参数，只适用于旧版本如 1.20）：
```bash
# ❌ 错误
app_process / com.genymobile.scrcpy.Server 3.3.4 debug 720 2000000 15 -1 true ...
```

**错误格式 #2**（没有版本号）：
```bash
# ❌ 错误
app_process / com.genymobile.scrcpy.Server scid=xxx log_level=debug ...
```

**错误格式 #3**（scid 参数名不对）：
```bash
# ❌ 错误
app_process / com.genymobile.scrcpy.Server 3.3.4 scid=xxx ...
```

**正确格式**：
```bash
# ✅ 正确
app_process / com.genymobile.scrcpy.Server 3.3.4 log_level=debug max_size=720 max_fps=15 stay_awake=true
```

---

### 坑 #3：连接方向搞反了！
**之前的理解**：
- scrcpy-server 在设备端监听
- 客户端（PC）连接过去
- 用 `adb forward` 方式

**实际情况**：
- scrcpy-server **主动连接**客户端！
- 所以需要：
  1. 客户端先监听端口
  2. 用 `adb reverse` 把设备端的 socket 转发到 PC 端端口
  3. 启动 server
  4. Accept 连接

**对比**：

| 方式 | 说明 | 结果 |
|------|------|-----|
| `adb forward tcp:port localabstract:scrcpy` | PC -> 设备 | ❌ Server 启动时会连接失败（Connection refused）|
| `adb reverse localabstract:scrcpy tcp:port` | 设备 -> PC | ✅ **正确！** |

---

### 坑 #4：tunnel_forward 和 scid 参数的困扰
**问题**：
- 看到 MYScrcpy 用了 `tunnel_forward=true` 和 `scid=xxx`
- 但是这些参数在 v3.3.4 上导致各种错误
- 或者是我们没有正确使用

**结论**：
- 对于简单场景，**不需要** tunnel_forward/scid！
- 用传统的 `adb reverse` + 默认 socket 名字 "scrcpy" 就能工作！

---

### 坑 #5：握手协议理解偏差
**问题**：
- 一开始以为 dummy byte 一定是 0x00
- 但在我们测试中收到的是 0x53 ('S')
- 可能不同版本有变化

**结论**：
- 不管 dummy byte 是什么，直接读就行了
- 关键是按顺序读取：1 + 64 + 4 + 4 字节

---

## scrcpy v3.3.4 支持的参数（部分）

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `log_level` | string | info | 日志级别: debug/info/warn/error |
| `max_size` | int | 0 | 最大尺寸（宽或高，0表示不限制） |
| `bit_rate` | int | 8000000 | 比特率 (bps) |
| `max_fps` | int | 0 | 最大帧率 |
| `stay_awake` | bool | false | 是否保持唤醒 |
| `crop` | string | - | 裁剪 (W:H:X:Y) |
| `lock_video_orientation` | int | -1 | 锁定方向: -1/0/1/2/3 |
| `display_id` | int | 0 | 显示 ID |

---

## 补充验证：async-adbc 的 API 支持

### ✅ async-adbc 的 reverse API 完全正常工作

**验证结果（2026-05-06）**：

| API 方法 | 状态 |
|----------|------|
| `device.reverse_remove_all()` | ✅ 工作正常 |
| `device.reverse(remote, local)` | ✅ 工作正常 |
| `device.reverse_list()` | ✅ 工作正常 |
| `device.reverse_remove(rule)` | ✅ 工作正常 |

### ✅ async-adbc 支持启动持续运行的 shell 命令

**关键发现**：
- 不要用 `await device.shell(cmd)` 启动 scrcpy-server！它会等待命令返回，而 server 会一直运行！
- 要用 `await device.shell_reader(cmd)`，它会立即返回一个 StreamReader，不等待命令结束！

**代码示例**：
```python
# ✅ 正确
reader = await device.shell_reader(cmd)
# 保持 reader 引用，server 就会持续运行

# ❌ 错误
await device.shell(cmd)  # 永远不会返回！
```

---

### 坑 #6: 持续运行的 shell 命令启动方式
**问题**：
- scrcpy-server 启动后持续运行，不会退出
- 用 `device.shell(cmd)` 会一直等待命令返回，导致程序卡死

**解决方案**：
- 用 `device.shell_reader(cmd)`！这个方法不会等待，立即返回一个 StreamReader
- 拿到 reader 之后不用 read（如果不关心输出），只要保持引用，进程就会持续运行

---

### 坑 #7: async-adbc reverse 的参数顺序
**问题**：
- `adb reverse` 命令行的顺序是：`adb reverse localabstract:scrcpy tcp:27183`
- 但 `device.reverse(remote, local)` 的参数顺序容易搞反！

**关键提示**：
看 `reverse` 方法的注释（第 331 行）：
> 注意：由于代理关系是反向的，所以 local 相当于设备的端口，remote 相当于 ADB Server 的主机端口。

看第 333 行：
> 等同于：adb reverse <remote> <local>

看第 345 行代码：
> `res = await self.request("reverse", "forward", f"{local};{remote}")`

**正确写法**：
```python
# 目标：设备 localabstract:scrcpy -> 主机 tcp:27183
# 等同于命令行：adb reverse localabstract:scrcpy tcp:27183

# ✅ 正确方式
await device.reverse("tcp:27183", "localabstract:scrcpy")

# ❌ 错误方式
await device.reverse("localabstract:scrcpy", "tcp:27183")

# 验证：调用 reverse_list() 看结果
rules = await device.reverse_list()
# 应该得到：local='localabstract:scrcpy', remote='tcp:27183'
```

---

## 完整验证代码示例

### 使用 async-adbc 验证成功的最小代码

```python
import asyncio
import socket
import os
from concurrent.futures import ThreadPoolExecutor
from async_adbc import ADBClient

async def main():
    adbc = ADBClient()
    device = (await adbc.devices())[0]

    # 1. 清理旧的 reverse
    await device.reverse_remove_all()

    # 2. 推送 server
    server_local = os.path.abspath("async_adbc/vendor/scrcpy/scrcpy-server-v3.3.4")
    server_remote = "/data/local/tmp/scrcpy-server"
    await device.push(server_local, server_remote)

    # 3. 先监听端口
    port = 27183
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.settimeout(15.0)
    server_sock.bind(("127.0.0.1", port))
    server_sock.listen(1)

    # 4. 设置 reverse (关键！参数顺序！)
    await device.reverse("tcp:27183", "localabstract:scrcpy")

    # 5. 启动 server (关键！用 shell_reader，不是 shell！)
    cmd = (
        f"CLASSPATH={server_remote} app_process / com.genymobile.scrcpy.Server"
        " 3.3.4 log_level=debug max_size=720 max_fps=15 stay_awake=true"
    )
    reader = await device.shell_reader(cmd)  # 不要 await shell(cmd)！！

    # 6. 接受连接
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        client_sock, addr = await loop.run_in_executor(executor, server_sock.accept)

        # 7. 握手
        dummy = await loop.run_in_executor(executor, lambda: client_sock.recv(1))
        device_name_bytes = await loop.run_in_executor(executor, lambda: client_sock.recv(64))
        width = int.from_bytes(await loop.run_in_executor(executor, lambda: client_sock.recv(4)), "big")
        height = int.from_bytes(await loop.run_in_executor(executor, lambda: client_sock.recv(4)), "big")

        # 8. 接收视频流
        client_sock.settimeout(0.1)
        total = 0
        start_time = loop.time()
        with open("output.h264", "wb") as f:
            while loop.time() - start_time < 5:
                try:
                    data = await loop.run_in_executor(executor, lambda: client_sock.recv(8192))
                    if data:
                        f.write(data)
                        total += len(data)
                except socket.timeout:
                    pass

        print(f"收到 {total} 字节")

        # 9. 清理
        client_sock.close()
        server_sock.close()
        await device.reverse_remove_all()
        await device.shell(f"rm {server_remote}")

asyncio.run(main())
```

---

## 文件清单

### 本次验证用到的文件
- `test_demo.py` - 完整预演脚本
- `convert_h264.py` - H.264 转 PNG 脚本
- `scrcpy_stream.h264` - 收到的视频流文件
- `frames/frame_0000.png` ~ `frames/frame_0009.png` - 截图
- `async_adbc/vendor/scrcpy/scrcpy-server-v3.3.4` - 真正的 server 文件

---

## 下一步计划

1. 把验证代码整合为 async-adbc 的 Scrcpy 插件
2. 支持异步收发
3. 支持控制命令（点击、滑动、按键）
4. 添加集成测试
5. 完善文档

---

## 参考链接

- **MYScrcpy** (参考项目): https://github.com/me2sy/MYScrcpy
- **scrcpy 官方**: https://github.com/Genymobile/scrcpy
- **scrcpy v3.3.4 Release**: https://github.com/Genymobile/scrcpy/releases/tag/v3.3.4
