# ADBClient

`ADBClient` 是 async-adbc 的核心类，用于与 ADB Server 通信。

## 构造函数

```python
ADBClient(host: str = "127.0.0.1", port: int = 5037)
```

创建一个新的 ADBClient 实例。

**参数：**
- `host` (str): ADB Server 主机地址，默认 `127.0.0.1`
- `port` (int): ADB Server 端口，默认 `5037`

**示例：**
```python
from async_adbc import ADBClient

adbc = ADBClient()  # 连接本地 ADB Server
# 或者连接远程
adbc = ADBClient("192.168.1.100", 5037)
```

## 方法

### version

```python
async def version() -> int
```

获取 ADB Server 版本号。

**等同于：** `adb version`

**返回：**
- `int`: ADB Server 版本号

**示例：**
```python
version = await adbc.version()
print(f"ADB 版本: {version}")
```

---

### kill

```python
async def kill()
```

杀死 ADB Server 进程。

**等同于：** `adb kill-server`

**示例：**
```python
await adbc.kill()
```

---

### devices

```python
async def devices(status: Status = Status.DEVICE) -> List[Device]
```

获取设备列表。

**等同于：** `adb devices -l`

**参数：**
- `status` (Status): 设备状态过滤，默认只返回 `Status.DEVICE`（已连接设备）

**返回：**
- `List[Device]`: 设备对象列表

**示例：**
```python
# 获取所有已连接设备
devices = await adbc.devices()

# 获取所有状态的设备
from async_adbc import Status
all_devices = await adbc.devices(status=None)
```

---

### device

```python
async def device(serialno: Optional[str] = None, status: Status = Status.DEVICE) -> Device
```

获取指定序列号的设备。

**参数：**
- `serialno` (str, optional): 设备序列号，为 `None` 时返回第一个设备
- `status` (Status): 设备状态过滤

**返回：**
- `Device`: 设备对象

**抛出：**
- `DeviceNotFoundError`: 设备不存在时抛出

**示例：**
```python
# 获取第一个设备
device = await adbc.device()

# 获取指定设备
device = await adbc.device("emulator-5554")
```

---

### devices_track

```python
async def devices_track() -> AsyncGenerator[DeviceStatusNotification, Any]
```

跟踪设备状态变化。

可以循环读取这个异步生成器，一旦设备状态改变就会返回一个通知消息。

**Yields：**
- `DeviceStatusNotification`: 设备状态通知对象

**示例：**
```python
async for notification in adbc.devices_track():
    print(f"设备 {notification.serialno} 状态变为 {notification.status}")
```

---

### transport

```python
async def transport(serialno: str) -> Connection
```

创建转发连接。

转发模式下的连接发送的请求都会直接转发到 Android 设备的 adbd 进程。

**参数：**
- `serialno` (str): 设备序列号

**返回：**
- `Connection`: 已切换到传输模式的连接

**示例：**
```python
conn = await adbc.transport("emulator-5554")
```

---

### remote_connect

```python
async def remote_connect(host: str, port: int) -> bool
```

远程连接设备。

**等同于：** `adb connect host:port`

**注意：** Android 设备要先用 `adb tcpip` 开启远程调试端口后才能 connect，本方法不会帮开调试端口。

**参数：**
- `host` (str): 主机 IP
- `port` (int): 端口

**返回：**
- `bool`: `True` 连接成功，`False` 连接失败

**示例：**
```python
success = await adbc.remote_connect("192.168.1.100", 5555)
```

---

### remote_disconnect

```python
async def remote_disconnect(host: str, port: int) -> str
```

断开远程设备。

**等同于：** `adb disconnect host:port`

**参数：**
- `host` (str): 主机 IP
- `port` (int): 端口

**返回：**
- `str`: 返回信息

**示例：**
```python
result = await adbc.remote_disconnect("192.168.1.100", 5555)
```

---

### forward_list

```python
async def forward_list() -> List[ForwardRule]
```

列出当前主机所有的转发规则列表。

**等同于：** `adb forward --list`

**返回：**
- `List[ForwardRule]`: 转发规则列表

**示例：**
```python
rules = await adbc.forward_list()
for rule in rules:
    print(f"{rule.serialno}: {rule.local} -> {rule.remote}")
```

---

### forward

```python
async def forward(serialno: str, local: str, remote: str, norebind: bool = False)
```

端口映射 / 正向代理。

**等同于：** `adb forward <local> <remote>`

**参数：**
- `serialno` (str): 设备序列号
- `local` (str): 本地地址
- `remote` (str): 远程地址
- `norebind` (bool): 是否不重新绑定

**示例：**
```python
# 映射本地 8080 端口到设备 80 端口
await adbc.forward("emulator-5554", "tcp:8080", "tcp:80")
```

---

### forward_remove

```python
async def forward_remove(serialno: str, local: Union[str, ForwardRule])
```

移除端口映射。

**等同于：** `adb forward --remove <local>`

**参数：**
- `serialno` (str): 设备序列号
- `local` (Union[str, ForwardRule]): 本地地址或 ForwardRule 对象

**示例：**
```python
await adbc.forward_remove("emulator-5554", "tcp:8080")
```

---

### forward_remove_all

```python
async def forward_remove_all()
```

移除所有设备所有端口映射。

**等同于：** `adb forward --remove-all`

**示例：**
```python
await adbc.forward_remove_all()
```

---

### close

```python
def close()
```

关闭连接，释放资源。

**示例：**
```python
adbc.close()
```

---

## 继承关系

`ADBClient` 继承自 `HostService`，`HostService` 继承自 `Service`。
