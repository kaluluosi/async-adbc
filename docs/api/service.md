# Service

Service 是 async-adbc 的抽象基类，定义了服务的基本接口。

## Service

抽象基类，所有服务的基类。

### 方法

#### create_connection

```python
@abstractmethod
async def create_connection() -> Connection
```

创建连接，子类必须实现。

**返回：**
- `Connection`: 连接对象

---

#### request

```python
async def request(*args: str) -> Response
```

发送请求并检查响应。

**参数：**
- `*args`: 请求参数

**返回：**
- `Response`: 响应对象

---

#### request_without_check

```python
async def request_without_check(*args: str) -> Response
```

发送请求但不检查响应。

**参数：**
- `*args`: 请求参数

**返回：**
- `Response`: 响应对象

---

#### close

```python
def close()
```

关闭连接，释放资源。

---

## HostService

继承自 `Service`，封装与 ADB Server 通信的命令。

参见 [ADBClient](./adbclient.md) 了解可用的方法。

---

## LocalService

继承自 `Service`，封装与设备通信的命令。

参见 [Device](./device.md) 了解可用的方法。

---

## Status

设备状态枚举。

```python
class Status(enum.Enum):
    DEVICE = "device"        # 设备已连接
    OFFLINE = "offline"      # 设备离线
    UNKNOWN = "unknown"      # 未知状态
    UNAUTHORIZED = "unauthorized"  # 设备未授权
    AUTHORIZING = "authorizing"    # 设备正在授权
```

---

## Connection

连接类，封装与 ADB Server 的 socket 连接。

### 方法

#### transport_mode

```python
async def transport_mode(serialno: str)
```

切换到传输模式。

**参数：**
- `serialno` (str): 设备序列号

---

#### request

```python
async def request(*args: str) -> Response
```

发送请求。

**参数：**
- `*args`: 请求参数

**返回：**
- `Response`: 响应对象

---

#### request_without_check

```python
async def request_without_check(*args: str) -> Response
```

发送请求但不检查响应。

**参数：**
- `*args`: 请求参数

**返回：**
- `Response`: 响应对象

---

#### close

```python
def close()
```

关闭连接。

---

## Response

响应类，封装响应读取。

### 属性

#### reader

```python
reader: StreamReader
```

异步读取器。

---

### 方法

#### text

```python
async def text() -> str
```

读取文本响应。

**返回：**
- `str`: 响应文本

---

#### read

```python
async def read(n: int = -1) -> bytes
```

读取字节响应。

**参数：**
- `n` (int): 读取字节数，`-1` 表示读取全部

**返回：**
- `bytes`: 响应字节

---

#### trace_text

```python
async def trace_text() -> AsyncGenerator[str, Any]
```

异步生成器，用于持续读取文本。

**Yields：**
- `str`: 文本行

---

#### close

```python
def close()
```

关闭响应。
