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

!!! warning
    **async-adbc** 只支持 Python 3.8 及以上版本

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

## 导航

- [快速入门](./quickstart.md) - 更详细的快速入门指南
- [API 参考](./api/adbclient.md) - 完整的 API 文档
- [插件列表](./plugins/index.md) - 所有可用插件
- [插件开发教程](./plugin-dev/guide.md) - 如何开发自己的插件
- [架构设计](./architecture/overview.md) - 了解内部实现

## 参考与感谢

- [adb 协议文档](https://github.com/kaluluosi/adbDocumentation/blob/master/README.zh-cn.md)
- [pure-python-adb](https://github.com/Swind/pure-python-adb)
- [solopi](https://github.com/alipay/SoloPi)
