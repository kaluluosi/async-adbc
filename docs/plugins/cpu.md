# CPUPlugin

CPU 插件，用于获取 CPU 信息和占用率。

**访问方式：** `device.cpu`

---

## 方法

### get_count

```python
@alru_cache
async def get_count(check: bool = False) -> int
```

获取 CPU 核心数。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `int`: 核心数

**示例：**
```python
count = await device.cpu.get_count()
print(f"CPU 核心数: {count}")
```

---

### get_freqs

```python
@alru_cache
async def get_freqs(check: bool = False) -> List[CPUFreq]
```

获取所有 CPU 的最小/当前/最大频率。

单位是 Hz。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `List[CPUFreq]`: CPU 频率列表

**CPUFreq 字段：**
- `min` (int): 最小频率
- `cur` (int): 当前频率
- `max` (int): 最大频率

**示例：**
```python
freqs = await device.cpu.get_freqs()
for i, freq in enumerate(freqs):
    print(f"CPU {i}: {freq.cur/1000000:.2f} GHz (min: {freq.min/1000000:.2f}, max: {freq.max/1000000:.2f})")
```

---

### get_normalize_factor

```python
@alru_cache
async def get_normalize_factor(check: bool = False) -> float
```

CPU 占用标准化因子。

使用这个因子乘以 CPU 占用率可以得到设备无关的标准化占用率。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `float`: 标准化因子

**示例：**
```python
factor = await device.cpu.get_normalize_factor()
print(f"标准化因子: {factor}")
```

---

### get_cpu_stats

```python
async def get_cpu_stats(check: bool = False) -> Dict[int, CPUStat]
```

通过解析 /proc/stat 获取每个核心的统计数据。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `Dict[int, CPUStat]`: 核心编号到统计数据的映射

**CPUStat 字段：**
- `user` (float): 用户态时间
- `nice` (float): 低优先级用户态时间
- `system` (float): 内核态时间
- `idle` (float): 空闲时间
- `iowait` (float): IO 等待时间
- `irq` (float): 硬中断时间
- `softirq` (float): 软中断时间
- `stealstolen` (float): 被偷取时间
- `guest` (float): 客户机时间
- `guest_nice` (float): 低优先级客户机时间

**CPUStat 属性：**
- `total`: 总时间
- `total_idle`: 总空闲时间
- `usage`: 占用率百分比

**示例：**
```python
stats = await device.cpu.get_cpu_stats()
for cpu_id, stat in stats.items():
    print(f"CPU {cpu_id}: {stat.usage:.2f}%")
```

---

### get_cpu_usages

```python
async def get_cpu_usages(check: bool = False) -> Dict[int, CPUUsage]
```

获取每个核心 CPU 占用率。

获取的是两次采样间隔的 CPU 占用率，第一次获取到的永远是 0，需要再调用一次才能获取到占用率。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `Dict[int, CPUUsage]`: 核心编号到占用率的映射

**CPUUsage 字段：**
- `usage` (float): 占用率百分比
- `normalized` (float): 标准化占用率

**示例：**
```python
# 第一次调用
await device.cpu.get_cpu_usages()

# 第二次调用获取真实占用率
usages = await device.cpu.get_cpu_usages()
for cpu_id, usage in usages.items():
    print(f"CPU {cpu_id}: {usage.usage:.2f}% (normalized: {usage.normalized:.2f}%)")
```

---

### get_total_cpu_stat

```python
async def get_total_cpu_stat(check: bool = False) -> CPUStat
```

获取总 CPU 统计数据。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `CPUStat`: CPU 统计数据

**示例：**
```python
stat = await device.cpu.get_total_cpu_stat()
print(f"总占用: {stat.usage:.2f}%")
```

---

### get_total_cpu_usage

```python
async def get_total_cpu_usage(check: bool = False) -> CPUUsage
```

获取总 CPU 占用率。

获取的是两次采样间隔的 CPU 占用率，第一次获取到的永远是 0，需要再调用一次才能获取到占用率。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `CPUUsage`: CPU 占用率

**示例：**
```python
# 第一次调用
await device.cpu.get_total_cpu_usage()

# 第二次调用获取真实占用率
usage = await device.cpu.get_total_cpu_usage()
print(f"总 CPU 占用: {usage.usage:.2f}% (normalized: {usage.normalized:.2f}%)")
```

---

### get_pid_cpu_stat

```python
async def get_pid_cpu_stat(pid_or_pkgname: Union[int, str], check: bool = False) -> ProcessCPUStat
```

通过 PID 或包名获取进程 CPU 统计数据。

**参数：**
- `pid_or_pkgname` (Union[int, str]): 进程 PID 或包名
- `check` (bool): 是否抛异常

**返回：**
- `ProcessCPUStat`: 进程 CPU 统计数据

**ProcessCPUStat 字段：**
- `name` (str): 进程名
- `utime` (int): 用户态时间
- `stime` (int): 内核态时间
- `cutime` (int): 子进程用户态时间
- `cstime` (int): 子进程内核态时间

**ProcessCPUStat 属性：**
- `total`: 总时间

**示例：**
```python
# 通过 PID
stat = await device.cpu.get_pid_cpu_stat(1234)

# 通过包名
stat = await device.cpu.get_pid_cpu_stat("com.example.app")
print(f"进程: {stat.name}")
print(f"总时间: {stat.total}")
```

---

### get_pid_cpu_usage

```python
async def get_pid_cpu_usage(pid_or_pkgname: Union[int, str], check: bool = False) -> CPUUsage
```

通过 PID 或包名获取进程 CPU 占用率。

**参数：**
- `pid_or_pkgname` (Union[int, str]): 进程 PID 或包名
- `check` (bool): 是否抛异常

**返回：**
- `CPUUsage`: CPU 占用率

**示例：**
```python
# 通过包名获取占用率
usage = await device.cpu.get_pid_cpu_usage("com.example.app")
print(f"进程 CPU 占用: {usage.usage:.2f}%")
```

---

### get_cpu_name

```python
@alru_cache
async def get_cpu_name(check: bool = False) -> str
```

获取 CPU 名称。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `str`: CPU 名称

**示例：**
```python
name = await device.cpu.get_cpu_name()
print(f"CPU: {name}")
```

---

### get_info

```python
@alru_cache
async def get_info(check: bool = False) -> CPUInfo
```

获取 CPU 信息。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `CPUInfo`: CPU 信息

**CPUInfo 字段：**
- `platform` (str): 平台
- `name` (str): CPU 名称
- `abi` (str): ABI
- `core` (int): 核心数
- `freq` (Tuple[int, int]): 频率 (min, max)

**示例：**
```python
info = await device.cpu.get_info()
print(f"平台: {info.platform}")
print(f"CPU: {info.name}")
print(f"核心: {info.core}")
print(f"频率范围: {info.freq[0]/1000000:.2f} - {info.freq[1]/1000000:.2f} GHz")
```
