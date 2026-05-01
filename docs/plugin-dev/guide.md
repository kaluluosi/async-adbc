# 插件开发教程

async-adbc 提供了灵活的插件机制，你可以轻松创建自己的插件来扩展功能。

## 基本结构

每个插件都需要继承 `Plugin` 基类，并使用 `@register_plugin` 装饰器注册。

```python
from async_adbc.plugin import Plugin, register_plugin

@register_plugin("myplugin", "myplugin")
class MyPlugin(Plugin):
    async def my_method(self):
        # 使用 self._device 访问 Device 对象
        result = await self._device.shell("some command")
        return result
```

## @register_plugin 装饰器

```python
def register_plugin(name: str, attr_name: str):
```

**参数：**
- `name` (str): 插件名称（用于内部标识）
- `attr_name` (str): Device 对象上的属性名（用户通过 `device.attr_name` 访问）

## Plugin 基类

```python
class Plugin:
    def __init__(self, device: Device):
        self._device = device
```

**属性：**
- `_device` (Device): 插件所属的 Device 对象，可以通过它访问其他插件和设备方法

## 完整示例

让我们创建一个简单的插件来获取设备的存储空间信息。

```python
# async_adbc/plugins/storage.py
import re
from typing import Dict
from pydantic import BaseModel
from async_adbc.plugin import Plugin, register_plugin

class StorageInfo(BaseModel):
    total: int = 0
    used: int = 0
    available: int = 0

@register_plugin("storage", "storage")
class StoragePlugin(Plugin):
    async def info(self, path: str = "/sdcard") -> StorageInfo:
        """获取存储空间信息"""
        result = await self._device.shell(f"df {path}")
        lines = result.splitlines()
        
        # 解析 df 输出
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 4:
                return StorageInfo(
                    total=int(parts[1]),
                    used=int(parts[2]),
                    available=int(parts[3])
                )
        
        return StorageInfo()
    
    async def list_dir(self, path: str = "/sdcard") -> Dict[str, str]:
        """列出目录内容"""
        result = await self._device.shell(f"ls -la {path}")
        return {"raw": result}
```

### 使用自定义插件

```python
from async_adbc import ADBClient
import asyncio

async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 使用自定义插件
    info = await device.storage.info("/sdcard")
    print(f"总空间: {info.total}")
    print(f"已用: {info.used}")
    print(f"可用: {info.available}")

asyncio.run(main())
```

## 插件发现机制

插件通过在 `async_adbc/plugins/__init__.py` 中导入实现自动发现和注册：

```python
# async_adbc/plugins/__init__.py
from . import storage  # noqa: F401
```

这样，当模块被导入时，`@register_plugin` 装饰器会自动执行，将插件注册到注册表中。

## 高级示例：带有缓存的插件

你可以使用 `async-lru` 库来缓存插件方法的结果。

```python
from async_lru import alru_cache
from async_adbc.plugin import Plugin, register_plugin

@register_plugin("example", "example")
class ExamplePlugin(Plugin):
    @alru_cache
    async def get_some_data(self):
        """这个方法的结果会被缓存"""
        result = await self._device.shell("some expensive command")
        return result
    
    async def clear_cache(self):
        """清除缓存"""
        self.get_some_data.cache_clear()
```

## 高级示例：使用其他插件

你的插件可以使用 Device 上已注册的其他插件。

```python
from async_adbc.plugin import Plugin, register_plugin

@register_plugin("performance", "performance")
class PerformancePlugin(Plugin):
    async def get_full_stats(self, package_name: str):
        """获取完整的性能统计"""
        # 使用 CPU 插件
        cpu_usage = await self._device.cpu.get_total_cpu_usage()
        
        # 使用内存插件
        mem_stat = await self._device.mem.stat(package_name)
        
        # 使用 FPS 插件
        fps_stat = await self._device.fps.stat(package_name)
        
        return {
            "cpu": cpu_usage,
            "mem": mem_stat,
            "fps": fps_stat
        }
```

## 最佳实践

1. **异步优先**：所有 I/O 操作都应该是异步的，使用 `async/await`
2. **使用数据模型**：使用 Pydantic 的 `BaseModel` 来定义返回的数据结构
3. **合理使用缓存**：对于不经常变化的数据，可以使用 `@alru_cache` 缓存
4. **错误处理**：适当处理错误，提供有用的错误信息
5. **文档注释**：为你的插件和方法添加详细的文档注释

## 完整项目结构

```
async_adbc/
├── plugin.py                  # 插件基类和注册装饰器
├── plugins/
│   ├── __init__.py           # 导入所有插件
│   ├── _registry.py          # 插件注册表
│   ├── pm.py                 # 内置插件
│   ├── cpu.py
│   └── storage.py            # 你的自定义插件
└── ...
```

## 测试插件

创建插件后，记得编写测试来验证功能：

```python
import pytest
from async_adbc import ADBClient

@pytest.mark.asyncio
@pytest.mark.integration
async def test_storage_plugin():
    adbc = ADBClient()
    device = await adbc.device()
    
    info = await device.storage.info()
    assert info.total > 0
    assert info.available > 0
```
