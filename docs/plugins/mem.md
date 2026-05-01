# MemPlugin

内存插件，用于获取设备和应用的内存信息。

**访问方式：** `device.mem`

---

## 方法

### get_info

```python
async def get_info(check: bool = False) -> MemInfo
```

获取设备内存信息。

单位是 kB。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `MemInfo`: 内存信息

**MemInfo 字段：**
- `mem_total` (int): 总内存
- `swap_total` (int): Swap 总大小

**示例：**
```python
info = await device.mem.get_info()
print(f"总内存: {info.mem_total} kB")
print(f"Swap: {info.swap_total} kB")
```

---

### stat

```python
async def stat(package_name: str, check: bool = False) -> MemStat
```

获取应用的内存统计信息。

单位是 kB。

**参数：**
- `package_name` (str): 包名
- `check` (bool): 是否抛异常

**返回：**
- `MemStat`: 内存统计信息

**MemStat 字段：**
- `pss` (int): 实际物理内存使用
- `private_dirty` (int): 私有脏内存
- `private_clean` (int): 私有干净内存
- `swapped_dirty` (int): 交换脏内存
- `heap_size` (int): 堆大小
- `heap_alloc` (int): 已分配堆
- `heap_free` (int): 空闲堆

**示例：**
```python
stat = await device.mem.stat("com.example.app")
print(f"PSS: {stat.pss} kB")
print(f"私有脏内存: {stat.private_dirty} kB")
print(f"堆大小: {stat.heap_size} kB")
```
