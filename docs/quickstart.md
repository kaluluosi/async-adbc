# 快速入门

## 安装

使用 pip 安装 async-adbc：

```shell
pip install async-adbc
```

## 基本使用

### 连接 ADB Server

首先创建一个 `ADBClient` 实例来连接本地的 ADB Server：

```python
import asyncio
from async_adbc import ADBClient

async def main():
    adbc = ADBClient()  # 默认连接 127.0.0.1:5037
    
    # 获取 ADB Server 版本
    version = await adbc.version()
    print(f"ADB 版本: {version}")

asyncio.run(main())
```

### 获取设备列表

```python
async def main():
    adbc = ADBClient()
    
    # 获取所有已连接设备
    devices = await adbc.devices()
    for device in devices:
        print(f"设备: {device.serialno}")
    
    # 获取第一个设备
    device = await adbc.device()
    print(f"默认设备: {device.serialno}")

asyncio.run(main())
```

### 使用 Device

`Device` 是与 Android 设备交互的主要接口。

#### 执行 Shell 命令

```python
async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 执行 shell 命令
    result = await device.shell("echo hello")
    print(result)  # 输出: hello
```

#### 文件传输

```python
async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 推送文件到设备
    await device.push("local/path/file.txt", "/sdcard/file.txt")
    
    # 从设备拉取文件
    await device.pull("/sdcard/file.txt", "local/path/file.txt")
```

### 使用插件

async-adbc 提供了丰富的插件来封装各种功能：

#### 获取设备属性

```python
async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 获取设备属性
    model = await device.prop.get("ro.product.model")
    print(f"设备型号: {model}")
    
    # 获取所有属性
    props = await device.prop.get_properties()
    print(props)
```

#### 包管理

```python
async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 列出已安装的包
    packages = await device.pm.list_packages()
    print(f"已安装 {len(packages)} 个应用")
    
    # 安装 APK
    await device.pm.install("path/to/app.apk")
    
    # 卸载应用
    await device.pm.uninstall("com.example.app")
    
    # 清除应用数据
    await device.pm.clear("com.example.app")
```

#### 获取性能数据

```python
async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # CPU 信息
    cpu_info = await device.cpu.get_info()
    print(f"CPU: {cpu_info.name}, {cpu_info.core} 核")
    
    # CPU 占用率
    cpu_usage = await device.cpu.get_total_cpu_usage()
    print(f"总 CPU 占用: {cpu_usage.usage:.2f}%")
    
    # 内存信息
    mem_info = await device.mem.get_info()
    print(f"总内存: {mem_info.mem_total} kB")
    
    # 应用内存占用
    mem_stat = await device.mem.stat("com.example.app")
    print(f"应用 PSS: {mem_stat.pss} kB")
    
    # 帧率统计
    fps_stat = await device.fps.stat("com.example.app")
    print(f"帧率: {fps_stat.fps:.2f} FPS")
```

#### 输入模拟

```python
async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 点击屏幕
    await device.input.tap(500, 500)
    
    # 滑动
    await device.input.swipe(100, 500, 500, 500, duration=300)
    
    # 按键
    await device.input.keyevent(3)  # HOME 键
    await device.input.keyevent("KEYCODE_BACK")  # 返回键
    
    # 输入文本
    await device.input.text("Hello World")
```

#### Logcat 日志

```python
async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 迭代日志
    async for line in device.logcat.logs():
        print(line.decode().strip())
```

### 完整示例

这是一个完整的示例，展示如何连接设备、获取信息和执行操作：

```python
import asyncio
from async_adbc import ADBClient

async def main():
    # 创建客户端
    adbc = ADBClient()
    
    try:
        # 获取设备
        device = await adbc.device()
        print(f"已连接设备: {device.serialno}")
        
        # 获取设备信息
        model = await device.prop.get("ro.product.model")
        android_version = await device.prop.get("ro.build.version.release")
        print(f"设备型号: {model}")
        print(f"Android 版本: {android_version}")
        
        # 列出已安装包
        packages = await device.pm.list_packages()
        print(f"已安装 {len(packages)} 个应用")
        
        # 获取 CPU 信息
        cpu_info = await device.cpu.get_info()
        print(f"CPU: {cpu_info.name} ({cpu_info.core} 核)")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        adbc.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 下一步

- 查看 [API 参考](./api/adbclient.md) 了解完整的 API 文档
- 查看 [插件列表](./plugins/index.md) 了解所有可用插件
- 查看 [架构概览](./architecture/overview.md) 了解内部实现
