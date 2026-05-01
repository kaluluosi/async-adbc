# LogcatPlugin

日志插件，用于获取设备日志。

**访问方式：** `device.logcat`

---

## 方法

### reader

```python
async def reader(*args: str) -> StreamReader
```

返回 logcat 的读取器，自行通过 readline 读取下一行。

**警告：** reader 需要手动关闭。

**参数：**
- `*args`: logcat 参数

**返回：**
- `StreamReader`: 异步读取器

**示例：**
```python
reader = await device.logcat.reader()
try:
    for _ in range(10):
        line = await reader.readline()
        print(line.decode())
finally:
    reader.feed_eof()
```

---

### logs

```python
async def logs(*args: str) -> AsyncGenerator[Any, str]
```

将 reader 封装成一个异步生成器，可以通过 async for 迭代每一行。

**参数：**
- `*args`: logcat 参数

**Yields：**
- `str`: 日志行

**示例：**
```python
# 迭代日志
i = 0
async for line in device.logcat.logs():
    print(line.decode())
    i += 1
    if i > 10:
        break
```
