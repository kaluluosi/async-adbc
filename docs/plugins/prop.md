# PropPlugin

属性插件，用于获取设备属性。

**访问方式：** `device.prop`

---

## 方法

### get_properties

```python
@alru_cache
async def get_properties(check: bool = False) -> Dict[str, str]
```

获取所有属性。

**参数：**
- `check` (bool): 是否抛异常

**返回：**
- `Dict[str, str]`: 属性字典

**示例：**
```python
props = await device.prop.get_properties()
print(f"设备型号: {props.get('ro.product.model')}")
print(f"Android 版本: {props.get('ro.build.version.release')}")
```

---

### get

```python
async def get(property_name: str, check: bool = False) -> str
```

获取属性。

**参数：**
- `property_name` (str): 属性名
- `check` (bool): 是否抛异常

**返回：**
- `str`: 属性值

**常用属性名：**
- `ro.product.model`: 设备型号
- `ro.product.brand`: 设备品牌
- `ro.build.version.release`: Android 版本
- `ro.build.version.sdk`: SDK 版本
- `ro.build.display.id`: 显示 ID
- `ro.product.cpu.abi`: CPU ABI

**示例：**
```python
model = await device.prop.get("ro.product.model")
print(f"设备型号: {model}")
```
