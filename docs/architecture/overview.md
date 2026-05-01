# async-adbc 架构概览

## 1. 核心概念

### 1.1 ADB 协议层次

async-adbc 直接与 ADB Server 通信，不依赖命令行 `adb` 工具。

```
┌─────────────────────────────────────────────────────────┐
│                   async-adbc (本库)                      │
├─────────────────────────────────────────────────────────┤
│              ADBClient (HOST SERVICE)                    │
├─────────────────────────────────────────────────────────┤
│              Device (LOCAL SERVICE)                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │
│  │  PM  │ │ Prop │ │ CPU  │ │ FPS  │ │ ...  │ (Plugins)│
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              ADB Server (localhost:5037)                 │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌───────────────────┐         ┌───────────────────┐
│  USB 连接设备     │         │  网络连接设备     │
│  (ADB Daemon)    │         │  (ADB Daemon)    │
└───────────────────┘         └───────────────────┘
```

### 1.2 服务分类

根据 ADB 协议文档，命令分为两类：

| 服务类型 | 说明 | 对应类 |
|---------|------|--------|
| **HOST SERVICE** | ADB Server 提供的服务 | `HostService` / `ADBClient` |
| **LOCAL SERVICE** | 设备 adbd 守护进程提供的服务 | `LocalService` / `Device` |

## 2. 核心类设计

### 2.1 类层次结构

```
Service (ABC)
├── HostService
│   └── ADBClient
└── LocalService
    └── Device

Plugin (ABC)
├── PMPlugin
├── PropPlugin
├── CPUPlugin
├── GPUPlugin
├── MemPlugin
├── FpsPlugin
├── ... (其他插件)
```

### 2.2 核心类职责

#### Service (抽象基类)
```python
class Service(ABC):
    @abstractmethod
    async def create_connection(self) -> Connection: ...

    async def request(self, *args: str) -> Response: ...
    async def request_without_check(self, *args: str) -> Response: ...
```

**职责**: 定义服务的基本接口，管理连接生命周期

#### HostService
**职责**: 封装与 ADB Server 通信的命令
- 获取/管理设备列表
- 端口转发 (forward)
- 远程连接 (connect/disconnect)
- 杀死 ADB Server

#### LocalService
**职责**: 封装与设备通信的命令
- Shell 命令执行
- 文件推送/拉取 (push/pull)
- 重启设备
- ADB 端口切换
- 反向代理 (reverse)

### 2.3 Connection 和 Response

#### Connection
- 封装与 ADB Server 的 socket 连接
- 实现协议打包/解包
- 提供 `request()` 方法发送命令

#### Response
- 封装响应读取
- 支持文本/二进制数据读取
- 支持流式追踪 (`trace()`)
- 实现上下文管理器协议

## 3. 插件系统设计 (v2.0)

### 3.1 注册流程

```
插件定义 (@register_plugin)
       │
       ▼
  插件注册表
       │
       ▼
 Device 初始化时动态加载
       │
       ▼
 device.plugin_name 可用
```

### 3.2 插件开发示例

```python
# plugins/hello.py
from async_adbc.plugin import Plugin, register_plugin

@register_plugin("hello", "hello")
class HelloPlugin(Plugin):
    async def say(self, name: str) -> str:
        result = await self._device.shell(f"echo Hello, {name}!")
        return result
```

使用:
```python
await device.hello.say("World")  # 返回 "Hello, World!"
```

## 4. 请求流程

### 4.1 HOST SERVICE 请求

```
ADBClient.request()
       │
       ▼
create_connection()
       │
       ▼
Connection.request("host:version")
       │
       ▼
发送: "001Chost:version"
       │
       ▼
接收: "OKAY" + "0004001B"
       │
       ▼
返回 Response 对象
```

### 4.2 LOCAL SERVICE 请求

```
Device.request()
       │
       ▼
ADBClient.create_connection()
       │
       ▼
Connection.transport_mode(serialno)
       │
       ▼
Connection.request("shell:echo hello")
       │
       ▼
返回 Response 对象
```

## 5. 数据流

### 5.1 Shell 命令

```
Device.shell("echo hello")
       │
       ▼
创建 Connection (transport mode)
       │
       ▼
发送: "0012shell:echo hello"
       │
       ▼
接收: "OKAY"
       │
       ▼
接收: "hello\n"
       │
       ▼
返回: "hello"
```

### 5.2 文件推送 (push)

```
Device.push(local_path, remote_path)
       │
       ▼
创建 Connection + sync: 模式
       │
       ▼
发送: SEND + remote_path,mode
       │
       ▼
发送: DATA + 数据块 (多次)
       │
       ▼
发送: DONE + mtime
       │
       ▼
接收: OKAY/FAIL
       │
       ▼
关闭连接
```

## 6. 异常层级

```
Exception
├── DeviceNotFoundError
│
├── PM 相关异常
│   ├── InstallError
│   ├── UninstallError
│   └── ClearError
│
└── FPS 相关异常
    └── SurfaceNotFoundError
```

## 7. 性能特性

### 7.1 缓存策略

- `Device.properties`: 使用 `@alru_cache` 缓存
- `CPUPlugin.count`: 使用 `@alru_cache` 缓存
- `CPUPlugin.freqs`: 使用 `@alru_cache` 缓存
- `CPUPlugin.cpu_name`: 使用 `@alru_cache` 缓存

### 7.2 并发优化

- `CPUPlugin.freqs`: 使用 `asyncio.gather()` 并行获取多个 CPU 频率
- `CPUPlugin.get_pid_cpu_usage`: 使用 `asyncio.gather()` 并行采样
