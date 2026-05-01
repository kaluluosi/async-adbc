# Device

`Device` 是与 Android 设备交互的主要接口，封装了所有设备操作功能。

## 属性

### serialno

```python
serialno: str
```

设备序列号。

---

### 插件属性

`Device` 会动态加载所有已注册的插件，以下是可用的插件属性：

| 属性 | 类型 | 说明 |
|------|------|------|
| `am` | `AMPlugin` | Activity Manager |
| `battery` | `BatteryPlugin` | 电池信息 |
| `cpu` | `CPUPlugin` | CPU 信息和占用率 |
| `forward` | `ForwardPlugin` | 端口转发 |
| `fps` | `FpsPlugin` | 帧率统计 |
| `gpu` | `GpuPlugin` | GPU 信息 |
| `input` | `InputPlugin` | 输入模拟 |
| `logcat` | `LogcatPlugin` | 日志 |
| `mem` | `MemPlugin` | 内存信息 |
| `minicap` | `MiniCapPlugin` | 截图 |
| `pm` | `PMPlugin` | 包管理 |
| `prop` | `PropPlugin` | 属性 |
| `temp` | `TempPlugin` | 温度 |
| `traffic` | `TrafficPlugin` | 流量统计 |
| `utils` | `UtilsPlugin` | 工具方法 |
| `wm` | `WMPlugin` | 窗口管理 |

---

## 方法

### shell_raw

```python
async def shell_raw(cmd: str, *args) -> bytes
```

调用 Android 设备的 shell 命令，返回原始字节。

**参数：**
- `cmd` (str): 命令
- `*args`: 命令参数

**返回：**
- `bytes`: 原始输出

**示例：**
```python
result = await device.shell_raw("ls /sdcard")
print(result)
```

---

### shell

```python
async def shell(cmd: str, *args: str) -> str
```

调用 Android 设备的 shell 命令。

**注意：** 如果命令是持续打印不会退出，比如 logcat，那么会导致这个方法无法退出。如果需要持续读取打印，应该用 `shell_reader`。

**等同于：** `adb shell`

**参数：**
- `cmd` (str): 命令
- `*args`: 命令参数

**返回：**
- `str`: 输出文本

**示例：**
```python
result = await device.shell("echo hello")
print(result)  # 输出: hello
```

---

### shell_reader

```python
async def shell_reader(cmd: str, *args) -> StreamReader
```

返回 shell 的读取器，用来持续读取打印。

**注意：** 属于底层方法，你可以用 `shell_raw` 返回的 Response 来获取 Reader，效果是一样的。

**警告：** reader 需要手动关闭。

**参数：**
- `cmd` (str): 命令
- `*args`: 命令参数

**返回：**
- `StreamReader`: 异步读取器

**示例：**
```python
reader = await device.shell_reader("logcat")
try:
    while not reader.at_eof():
        line = await reader.readline()
        print(line.decode())
finally:
    reader.feed_eof()
```

---

### adbd_tcpip

```python
async def adbd_tcpip(port: int) -> str
```

开启 adbd 远程调试端口。

**等同于：** `adb tcpip <port>`

**参数：**
- `port` (int): 端口

**返回：**
- `str`: 返回信息

**示例：**
```python
result = await device.adbd_tcpip(5555)
print(result)
```

---

### adbd_root

```python
async def adbd_root()
```

让设备上的 adbd 进程以 root 权限启动。

**注意：** 这个方法调用后会导致 ADB 短暂无法与设备通信。

**示例：**
```python
await device.adbd_root()
```

---

### adbd_unroot

```python
async def adbd_unroot()
```

让设备上的 adbd 进程取消 root 权限。

**注意：** 这个方法调用后会导致 ADB 短暂无法与设备通信。

**示例：**
```python
await device.adbd_unroot()
```

---

### reboot

```python
async def reboot(
    wait_for: bool = True,
    timeout: int = 60,
    wait_interval: int = 1,
    option: Optional[str] = None,
)
```

重启设备。

**参数：**
- `wait_for` (bool): 是否等待重启完成
- `timeout` (int): 超时时间（秒）
- `wait_interval` (int): 等待间隔（秒）
- `option` (str, optional): 重启选项，可选 `bootloader`、`recovery`、`sideload`、`sideload-auto-reboot`

**示例：**
```python
# 正常重启并等待
await device.reboot()

# 重启到 recovery
await device.reboot(option="recovery")

# 不等待
await device.reboot(wait_for=False)
```

---

### wait_shutdown

```python
async def wait_shutdown(timeout: int, wait_interval: int)
```

等待设备关机。

**参数：**
- `timeout` (int): 超时时间（秒）
- `wait_interval` (int): 等待间隔（秒）

**示例：**
```python
await device.wait_shutdown(60, 1)
```

---

### wait_boot_complete

```python
async def wait_boot_complete(timeout: int = 60, wait_interval: int = 1)
```

等待设备启动完成。

**参数：**
- `timeout` (int): 超时时间（秒）
- `wait_interval` (int): 等待间隔（秒）

**示例：**
```python
await device.wait_boot_complete(60, 1)
```

---

### remount

```python
async def remount() -> str
```

重新挂载系统分区为可读写。

remount 是一种 adb 命令，用于请求 adbd 将设备的文件系统重新挂载为可读写模式，而不是只读模式。默认情况下 `/system` 目录是只读的，非 root 用户无权限写入，remount 就是重新挂载为可写。通常，在执行 adb sync 或 adb push 请求之前，都需要使用这种命令。但是，由于非 root 设备不允许这种操作，所以这种请求可能不会成功。

**等同于：** `adb remount`

**返回：**
- `str`: 返回信息

**抛出：**
- `RuntimeError`: 挂载失败时抛出

**示例：**
```python
result = await device.remount()
print(result)
```

---

### push

```python
async def push(
    src: str,
    dst: str,
    chmod: int = 0o644,
    progress_cb: Optional[ProgressCallback] = None,
)
```

推送本地文件到设备。

如果这个文件的父目录不存在，也会自动帮其创建父目录。只支持文件，不支持目录。

**等同于：** `adb push src dst`

**参数：**
- `src` (str): 源文件路径
- `dst` (str): 目标文件路径
- `chmod` (int): 文件权限，默认 `0o644`
- `progress_cb` (ProgressCallback, optional): 进度回调函数，参数为 `(src, total, sent)`

**示例：**
```python
# 简单推送
await device.push("local.txt", "/sdcard/local.txt")

# 带进度回调
def progress(src, total, sent):
    print(f"上传进度: {sent / total * 100:.1f}%")

await device.push("local.txt", "/sdcard/local.txt", progress_cb=progress)
```

---

### pull

```python
async def pull(src: str, dst: str)
```

从设备拉取文件到本地。

只支持文件，不支持拉整个目录。

**等同于：** `adb pull src dst`

**参数：**
- `src` (str): 源文件路径
- `dst` (str): 目标文件路径

**示例：**
```python
await device.pull("/sdcard/remote.txt", "local.txt")
```

---

### reverse_list

```python
async def reverse_list() -> List[ReverseRule]
```

列出当前设备的反向代理规则列表。

返回的一定是当前设备的代理规则。

**等同于：** `adb reverse --list`

**返回：**
- `List[ReverseRule]`: 反向代理规则列表

**示例：**
```python
rules = await device.reverse_list()
for rule in rules:
    print(f"{rule.remote} -> {rule.local}")
```

---

### reverse

```python
async def reverse(remote: str, local: str, norebind: bool = False)
```

反向代理。

**注意：** 由于代理关系是反向的，所以 local 相当于设备的端口，remote 相当于 ADB Server 的主机端口。

**等同于：** `adb reverse <remote> <local>`

**参数：**
- `remote` (str): 远程地址（主机端）
- `local` (str): 本地地址（设备端）
- `norebind` (bool): 是否不重新绑定

**示例：**
```python
# 设备 9000 端口反向代理到主机 8000 端口
await device.reverse("tcp:8000", "tcp:9000")
```

---

### reverse_remove

```python
async def reverse_remove(local: Union[str, ReverseRule])
```

移除反向代理。

**等同于：** `adb reverse --remove <local>`

**参数：**
- `local` (Union[str, ReverseRule]): 本地地址（设备端）或 ReverseRule 对象

**示例：**
```python
await device.reverse_remove("tcp:9000")
```

---

### reverse_remove_all

```python
async def reverse_remove_all()
```

移除所有反向代理规则。

**等同于：** `adb reverse --remove-all`

**示例：**
```python
await device.reverse_remove_all()
```

---

### create_connection

```python
async def create_connection() -> Connection
```

创建并切换到传输模式的连接。

**返回：**
- `Connection`: 已切换到传输模式的连接

---

### get_properties

```python
@alru_cache
async def get_properties() -> Dict[str, str]
```

获取设备属性。

**返回：**
- `Dict[str, str]`: 设备属性字典

**示例：**
```python
props = await device.get_properties()
print(props.get("ro.product.model"))
```

---

### get_pid_by_pkgname

```python
async def get_pid_by_pkgname(package_name: str) -> int
```

通过包名获取进程 PID。

**参数：**
- `package_name` (str): 应用包名

**返回：**
- `int`: 进程 PID

**抛出：**
- `ValueError`: 应用没有运行时抛出

**示例：**
```python
pid = await device.get_pid_by_pkgname("com.example.app")
print(pid)
```

---

### file_exists

```python
async def file_exists(file_path: str) -> bool
```

判断设备上是否存在这个文件路径。

**参数：**
- `file_path` (str): 文件路径

**返回：**
- `bool`: `True` 存在，`False` 不存在

**示例：**
```python
exists = await device.file_exists("/sdcard/file.txt")
print(exists)
```

---

### close

```python
def close()
```

关闭设备连接，释放资源。

**示例：**
```python
device.close()
```

---

## 继承关系

`Device` 继承自 `LocalService`，`LocalService` 继承自 `Service`。
