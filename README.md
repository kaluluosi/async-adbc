# async-adbc

[![CI](https://github.com/kaluluosi/async-adbc/actions/workflows/ci.yml/badge.svg)](https://github.com/kaluluosi/async-adbc/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/async-adbc.svg)](https://badge.fury.io/py/async-adbc)
[![Python versions](https://img.shields.io/pypi/pyversions/async-adbc.svg)](https://pypi.org/project/async-adbc/)

**async-adbc** 是 ADB Client 的纯 Python 异步实现，直接与 ADB Server 通信，无需通过进程调用命令行执行 ADB 命令。

## 特性

- ⚡ **异步优先**：完全异步的 API 设计，基于 asyncio
- 📱 **设备管理**：连接、管理多个 Android 设备
- 🔌 **丰富插件**：17+ 内置插件，覆盖各种功能
- 🚀 **高性能**：直接与 ADB Server 通信，无需命令行
- 📦 **插件系统**：灵活的插件机制，易于扩展
- 🐍 **Python 3.8+**：支持 Python 3.8 及以上版本

## 安装

```shell
pip install async-adbc
```

## 快速入门

### 使用 ADBClient

```python
import asyncio
from async_adbc import ADBClient

async def main():
    adbc = ADBClient()  # 默认连接 127.0.0.1:5037
    
    # 获取 ADB 版本
    version = await adbc.version()
    print(f"ADB 版本: {version}")
    
    # 获取设备列表
    devices = await adbc.devices()
    for device in devices:
        print(f"设备: {device.serialno}")
    
    # 获取第一个设备
    device = await adbc.device()
    print(f"默认设备: {device.serialno}")

asyncio.run(main())
```

### 使用 Device 插件

```python
import asyncio
from async_adbc import ADBClient

async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 执行 shell 命令
    result = await device.shell("echo hello")
    print(f"Shell 输出: {result}")
    
    # 获取设备属性
    model = await device.prop.get("ro.product.model")
    print(f"设备型号: {model}")
    
    # 列出已安装的包
    packages = await device.pm.list_packages()
    print(f"已安装 {len(packages)} 个应用")
    
    # 获取 CPU 信息
    cpu_info = await device.cpu.get_info()
    print(f"CPU: {cpu_info.name}, {cpu_info.core} 核")
    
    # 获取帧率
    fps_stat = await device.fps.stat("com.example.app")
    print(f"FPS: {fps_stat.fps:.2f}")
    
    # 模拟点击
    await device.input.tap(500, 500)

asyncio.run(main())
```

## 文档

完整文档请访问：[https://kaluluosi.github.io/async-adbc/](https://kaluluosi.github.io/async-adbc/)

- [快速入门](https://kaluluosi.github.io/async-adbc/quickstart/)
- [API 参考](https://kaluluosi.github.io/async-adbc/api/adbclient/)
- [插件列表](https://kaluluosi.github.io/async-adbc/plugins/)
- [插件开发教程](https://kaluluosi.github.io/async-adbc/plugin-dev/guide/)
- [架构设计](https://kaluluosi.github.io/async-adbc/architecture/overview/)

## 内置插件

| 插件 | 说明 |
|------|------|
| `device.am` | Activity Manager，应用启动和停止 |
| `device.battery` | 电池信息 |
| `device.cpu` | CPU 信息和占用率 |
| `device.forward` | 端口转发 |
| `device.fps` | 帧率统计 |
| `device.gpu` | GPU 信息 |
| `device.input` | 输入模拟（点击、滑动、按键等） |
| `device.logcat` | 日志 |
| `device.mem` | 内存信息 |
| `device.minicap` | 截图（高效） |
| `device.pm` | 包管理（安装、卸载、列出包等） |
| `device.prop` | 属性（获取设备属性） |
| `device.temp` | 温度 |
| `device.traffic` | 流量统计 |
| `device.utils` | 工具方法 |
| `device.wm` | 窗口管理（分辨率、方向） |

## 示例

### 文件传输

```python
# 推送文件到设备
await device.push("local.txt", "/sdcard/local.txt")

# 从设备拉取文件
await device.pull("/sdcard/remote.txt", "local.txt")
```

### 应用管理

```python
# 安装 APK
await device.pm.install("app.apk")

# 卸载应用
await device.pm.uninstall("com.example.app")

# 清除应用数据
await device.pm.clear("com.example.app")
```

### 性能监控

```python
# 获取 CPU 占用率
cpu_usage = await device.cpu.get_total_cpu_usage()
print(f"CPU: {cpu_usage.usage:.2f}%")

# 获取内存信息
mem_stat = await device.mem.stat("com.example.app")
print(f"PSS: {mem_stat.pss} kB")

# 获取帧率
fps_stat = await device.fps.stat("com.example.app")
print(f"FPS: {fps_stat.fps:.2f}")
```

## 项目结构

```
async_adbc/
├── __init__.py          # 导出主要类
├── client.py            # ADBClient 实现
├── device.py            # Device 实现
├── plugin.py            # 插件基类
├── plugins/             # 插件目录
│   ├── __init__.py
│   ├── _registry.py     # 插件注册表
│   ├── am.py            # Activity Manager
│   ├── battery.py       # 电池
│   ├── cpu.py           # CPU
│   ├── fps.py           # 帧率
│   ├── input.py         # 输入
│   ├── mem.py           # 内存
│   ├── pm.py            # 包管理
│   ├── prop.py          # 属性
│   └── ...
├── protocol/            # 协议实现
│   ├── __init__.py
│   ├── consts.py        # 协议常量
│   ├── connection.py    # 连接管理
│   └── response.py      # 响应处理
├── service/             # 服务实现
│   ├── __init__.py
│   ├── base.py          # 服务基类
│   ├── host.py          # Host 服务
│   └── local.py         # Local 服务
├── exceptions.py        # 异常定义
├── models.py            # 数据模型
└── config.py            # 配置
```

## 开发

### 克隆代码

```shell
git clone https://github.com/kaluluosi/async-adbc.git
cd async-adbc
```

### 安装依赖

```shell
pip install -e ".[test,docs]"
```

### 运行测试

```shell
# 运行单元测试
pytest -m unit

# 运行集成测试（需要连接设备）
pytest -m integration
```

### 构建文档

```shell
mkdocs serve
```

## 参考与感谢

- [adb 协议文档](https://github.com/kaluluosi/adbDocumentation/blob/master/README.zh-cn.md)
- [pure-python-adb](https://github.com/Swind/pure-python-adb)
- [solopi](https://github.com/alipay/SoloPi)

## 许可证

MIT License

---

## 英文说明 / English

### async-adbc

**async-adbc** is a pure Python asynchronous ADB Client implementation that communicates directly with ADB Server, eliminating the need for command-line invocation.

### Features

- ⚡ **Async-first**: Fully asynchronous API based on asyncio
- 📱 **Device management**: Connect and manage multiple Android devices
- 🔌 **Rich plugins**: 17+ built-in plugins covering various functionalities
- 🚀 **High performance**: Direct communication with ADB Server
- 📦 **Extensible**: Flexible plugin system for easy extension
- 🐍 **Python 3.8+**: Supports Python 3.8 and above

### Quick Example

```python
import asyncio
from async_adbc import ADBClient

async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # Execute shell command
    result = await device.shell("echo hello")
    print(result)
    
    # Get device properties
    model = await device.prop.get("ro.product.model")
    print(f"Model: {model}")
    
    # List packages
    packages = await device.pm.list_packages()
    print(f"Installed: {len(packages)}")
    
    # Get CPU info
    cpu_info = await device.cpu.get_info()
    print(f"CPU: {cpu_info.name}")

asyncio.run(main())
```

### License

MIT License
