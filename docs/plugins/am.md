# AMPlugin (Activity Manager)

Activity Manager 插件，用于启动和停止应用。

**访问方式：** `device.am`

---

## 方法

### start_app

```python
async def start_app(package_name: str, activity: Optional[str] = None)
```

启动应用。

这个方法能够支持直接打开应用的某个 Activity。

**参数：**
- `package_name` (str): 包名
- `activity` (str, optional): 目标 Activity，默认为 None（启动主 Activity）

**示例：**
```python
# 启动主 Activity
await device.am.start_app("com.example.app")

# 启动指定 Activity
await device.am.start_app("com.example.app", "SettingsActivity")
```

---

### stop_app

```python
async def stop_app(package_name: str)
```

关闭应用。

**参数：**
- `package_name` (str): 包名

**示例：**
```python
await device.am.stop_app("com.example.app")
```
