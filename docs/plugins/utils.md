# UtilsPlugin

工具函数插件，包含一些不好分类的工具函数。

**访问方式：** `device.utils`

---

## 方法

### screencap

```python
async def screencap(save_file: Optional[str] = None) -> bytes
```

原生截屏，效率很慢，建议用 minicap 代替。

**参数：**
- `save_file` (str, optional): 保存文件，PNG 格式，为空就不保存

**返回：**
- `bytes`: 返回二进制数据

**示例：**
```python
# 只获取二进制数据
data = await device.utils.screencap()

# 保存到文件
data = await device.utils.screencap("screenshot.png")
```
