# 代码问题清单

本文档记录 async-adbc 代码库中发现的具体问题，按优先级和类别组织。

## 🔴 高优先级

### 1. Device 类硬编码插件

**位置**: `device.py:46-61`

**问题描述**:
```python
self.pm = PMPlugin(self)
self.prop = PropPlugin(self)
self.cpu = CPUPlugin(self)
self.gpu = GPUPlugin(self)
self.mem = MemPlugin(self)
self.fps = FpsPlugin(self)
self.battery = BatteryPlugin(self)
self.temp = TempPlugin(self)
self.utils = UtilsPlugin(self)
self.traffic = TrafficPlugin(self)
self.am = ActivityManagerPlugin(self)
self.forward = ForwardPlugin(self)
self.logcat = LogcatPlugin(self)
# self.minicap = MinicapPlugin(self)
self.wm = WMPlugin(self)
self.input = InputPlugin(self)
```

**影响**:
- 新增插件必须修改 Device 类
- 违反开闭原则 (OCP)
- 无法动态启用/禁用插件

**建议**: 使用插件注册表机制

---

### 2. 异常定义分散

**位置**:
- `service/host.py:11-13` - `DeviceNotFoundError`
- `plugins/pm.py:6-21` - `InstallError`, `UninstallError`, `ClearError`
- `plugins/fps.py:6-7` - `SurfaceNotFoundError`

**问题描述**:
异常类分散在多个文件中，但通过 `exceptions.py` 统一导出，导致：
- 异常定义位置不直观
- 新增异常需要记住导出
- 难以一览所有异常

**建议**: 将所有异常移到 `exceptions.py` 统一定义

---

### 3. 数据模型分散

**位置**:
- `service/host.py:16-44` - `DeviceStatusNotification`, `ForwardRule`, `ReverseRule`
- `plugins/fps.py:10-15` - `FpsStat`
- `plugins/cpu.py:16-140` - `CPUInfo`, `CPUUsage`, `CPUFreq`, `CPUStat`, `ProcessCPUStat`
- `plugins/mem.py:6-19` - `MemInfo`, `MemStat`

**问题描述**:
Pydantic 模型类分散在多个模块中，导入关系复杂。

**建议**: 创建 `models.py` 统一存放所有数据模型

---

### 4. protocol.py 单文件过大

**位置**: `protocol.py` (约 500 行)

**问题描述**:
文件包含：
- 协议常量 (20 行)
- 工具函数 (20 行)
- `Response` 类 (100 行)
- `Connection` 类 (250 行)

**建议**: 拆分为 `protocol/consts.py`, `protocol/connection.py`, `protocol/response.py`

---

## 🟡 中优先级

### 5. 循环依赖风险

**位置**: `service/host.py` ↔ `device.py`

**问题描述**:
```python
# service/host.py
from async_adbc.device import Device, Status  # 类型注解用

# device.py
if typing.TYPE_CHECKING:
    from async_adbc.adbclient import ADBClient
```

虽然目前通过 `TYPE_CHECKING` 避免了运行时循环依赖，但这增加了代码复杂度。

**建议**: 重构模块边界，消除潜在循环依赖

---

### 6. 重复的 properties 实现

**位置**:
- `device.py:68-87` - `Device.properties`
- `plugins/prop.py:8-23` - `PropPlugin.properties`

**问题描述**:
两个不同的 `properties` 属性实现了相同功能，容易混淆。

**代码**:
```python
# device.py
@property
@alru_cache
async def properties(self) -> Dict[str, str]:
    res = await self.shell("getprop")
    # ... 解析

# plugins/prop.py
@property
async def properties(self) -> Dict[str, str]:
    res = await self._device.shell("getprop")
    # ... 解析
```

**建议**: 统一使用一个实现，另一个作为别名或废弃

---

### 7. 拼写错误: "row" vs "raw"

**位置**: `service/local.py:26`

**问题描述**:
```python
async def shell_raw(self, cmd: str, *args) -> bytes:
```

方法名是正确的 `shell_raw`，但文档注释中可能有笔误。建议检查所有文档字符串。

---

### 8. CPUPlugin 中的硬编码 sleep

**位置**:
- `plugins/cpu.py:276` - `await asyncio.sleep(0.1)`
- `plugins/cpu.py:336` - `await asyncio.sleep(0.1)`
- `plugins/cpu.py:435` - `await asyncio.sleep(0.1)`

**问题描述**:
采样间隔硬编码为 0.1 秒，无法自定义。

**建议**: 将采样间隔作为可配置参数

---

### 9. TODO 注释未处理

**位置**: `plugins/cpu.py:175`

```python
# TODO: 模拟器可能没有这个路径，有没有兼容性更强的方案来获取CPU频率
```

**建议**: 创建 issue 跟踪，或实现替代方案

---

### 10. 注释掉的代码

**位置**:
- `device.py:59` - `# self.minicap = MinicapPlugin(self)`
- `tests/test_device.py:36` - `@unittest.skip(...)`
- `tests/test_device.py:88` - `@unittest.skip(...)`
- `tests/test_device.py:94` - `@unittest.skip(...)`
- `tests/test_device.py:101` - `@unittest.skip(...)`
- `tests/test_device.py:105` - `@unittest.skip(...)`

**问题描述**:
注释掉的代码影响可读性，应该删除或有明确说明。

---

### 11. 魔法数字

**位置**:
- `service/local.py:23` - `DATA_MAX_LENGTH = 65536`
- `service/local.py:22` - `TEMP_PATH = "/data/local/tmp"`
- `plugins/fps.py:113` - `83.33`
- `plugins/fps.py:116` - `125`

**建议**: 将这些常量移到 `config.py` 统一管理

---

## 🟢 低优先级

### 12. 文档字符串格式不统一

**问题描述**:
部分函数有详尽的 docstring，部分没有，格式也不统一。

**建议**: 采用 Google 或 NumPy 风格统一 docstring 格式

---

### 13. 类型注解可以更完善

**位置**: 多处

**问题描述**:
部分函数缺少返回类型注解。

**示例**:
```python
async def shell_reader(self, cmd: str, *args) -> StreamReader:  # 有注解
async def adbd_root(self):  # 缺少注解
```

---

### 14. 日志缺失

**问题描述**:
代码库中几乎没有使用 `logging`，调试困难。

**建议**: 添加可选的调试日志

---

### 15. 测试覆盖率可提升

**问题描述**:
部分边缘情况缺少测试，错误路径测试不足。

---

## 📊 问题统计

| 优先级 | 数量 |
|--------|------|
| 🔴 高 | 4 |
| 🟡 中 | 7 |
| 🟢 低 | 4 |
| **总计** | **15** |

## 🎯 建议修复顺序

1. 先处理高优先级问题 (重构核心架构)
2. 再处理中优先级问题 (改进代码质量)
3. 最后处理低优先级问题 ( polish 细节)
