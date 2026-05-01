# 异常

## DeviceNotFoundError

设备不存在异常。

```python
class DeviceNotFoundError(Exception):
    def __init__(self, serialno: str, *args: object)
```

**参数：**
- `serialno` (str): 设备序列号

**抛出场景：**
- `ADBClient.device()`: 找不到指定设备时

**示例：**
```python
from async_adbc import ADBClient
from async_adbc.exceptions import DeviceNotFoundError

try:
    device = await adbc.device("non-existent")
except DeviceNotFoundError as e:
    print(f"设备未找到: {e}")
```

---

## InstallError

应用安装失败异常。

```python
class InstallError(Exception):
    def __init__(self, src: str, msg)
```

**参数：**
- `src` (str): APK 文件路径
- `msg`: 错误消息

**抛出场景：**
- `PMPlugin.install()`: 安装失败时

**示例：**
```python
from async_adbc.exceptions import InstallError

try:
    await device.pm.install("app.apk")
except InstallError as e:
    print(f"安装失败: {e}")
```

---

## UninstallError

应用卸载失败异常。

```python
class UninstallError(Exception):
    def __init__(self, *args: object)
```

**抛出场景：**
- `PMPlugin.uninstall()`: 卸载失败时

**示例：**
```python
from async_adbc.exceptions import UninstallError

try:
    await device.pm.uninstall("com.example.app")
except UninstallError as e:
    print(f"卸载失败: {e}")
```

---

## ClearError

应用数据清除失败异常。

```python
class ClearError(Exception):
    def __init__(self, package_name: str, msg)
```

**参数：**
- `package_name` (str): 应用包名
- `msg`: 错误消息

**抛出场景：**
- `PMPlugin.clear()`: 清除失败时

**示例：**
```python
from async_adbc.exceptions import ClearError

try:
    await device.pm.clear("com.example.app")
except ClearError as e:
    print(f"清除失败: {e}")
```

---

## SurfaceNotFoundError

找不到 Surface 异常。

```python
class SurfaceNotFoundError(Exception):
    pass
```

**抛出场景：**
- `FpsPlugin.stat()`: 找不到 Surface 时（虽然当前实现不会抛出，而是返回 0 FPS）
