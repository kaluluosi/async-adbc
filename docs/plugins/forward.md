# ForwardPlugin

端口转发插件，作用在当前设备上。

与 ADBClient 的 forward 方法区别在于 Device 的 forward 方法都是作用在当前设备，可以理解为方法参数中 serialno 已经默认传入了 Device 的 serialno。

**访问方式：** `device.forward`

---

## 方法

### forward_list

```python
async def forward_list() -> List[ForwardRule]
```

列出当前设备的所有转发规则。

**返回：**
- `List[ForwardRule]`: 转发规则列表

**ForwardRule 字段：**
- `serialno` (str): 设备序列号
- `local` (str): 本地地址
- `remote` (str): 远程地址

**示例：**
```python
rules = await device.forward.forward_list()
for rule in rules:
    print(f"{rule.local} -> {rule.remote}")
```

---

### forward

```python
async def forward(local: str, remote: str, norebind: bool = False)
```

设置端口映射。

**参数：**
- `local` (str): 本地地址
- `remote` (str): 远程地址
- `norebind` (bool): 是否不重新绑定

**示例：**
```python
# 映射本地 8080 端口到设备 80 端口
await device.forward.forward("tcp:8080", "tcp:80")
```

---

### forward_remove

```python
async def forward_remove(local: Union[str, ForwardRule])
```

移除端口映射。

**参数：**
- `local` (Union[str, ForwardRule]): 本地地址或 ForwardRule 对象

**示例：**
```python
await device.forward.forward_remove("tcp:8080")
```

---

### forward_remove_all

```python
async def forward_remove_all()
```

移除当前设备的所有端口映射。

**示例：**
```python
await device.forward.forward_remove_all()
```
