# GPUPlugin

GPU 信息插件，用于获取 GPU 信息。

**访问方式：** `device.gpu`

---

## 方法

### get_info

```python
async def get_info(check: bool = False) -> GPUInfo
```

获取 GPU 信息。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `GPUInfo`: GPU 信息

**GPUInfo 字段：**
- `manufactor` (str): 制造商
- `name` (str): GPU 名称
- `opengl` (str): OpenGL 版本

**示例：**
```python
info = await device.gpu.get_info()
print(f"制造商: {info.manufactor}")
print(f"GPU: {info.name}")
print(f"OpenGL: {info.opengl}")
```
