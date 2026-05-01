# PMPlugin (Package Manager)

包管理插件，用于安装、卸载、列出应用等操作。

**访问方式：** `device.pm`

---

## 方法

### list_packages

```python
async def list_packages() -> List[str]
```

列出已安装的包。

**等同于：** `adb shell pm list packages`

**返回：**
- `List[str]`: 包名列表

**示例：**
```python
packages = await device.pm.list_packages()
print(f"已安装 {len(packages)} 个应用")
for pkg in packages[:10]:
    print(pkg)
```

---

### install

```python
async def install(path: str, args: str = "rd", progress_cb: Optional[ProgressCallback] = None) -> bool
```

将路径的 APK 文件推送并用 pm install 安装到手机里。

**等同于：** `adb install path`

**args 参数说明：**
- `t`: 以测试版本安装应用
- `l`: 单向锁定该应用程序（不能提取 APK，不能手机里卸载，相当于内置 app 了，需要 root 权限）
- `s`: 把 APK 安装到 SD 卡上
- `g`: 安装的时候允许所有权限（安装完后不用手动授予各种权限弹窗了，直接默认全给了）
- `r`: 强制覆盖安装（不卸载原来的应用重复安装会失败，用这个参数可以直接覆盖）
- `d`: 无视版本号（允许低版本覆盖高版本）

**参数：**
- `path` (str): APK 文件路径
- `args` (str): 安装参数，默认 "rd"
- `progress_cb` (ProgressCallback, optional): 进度回调函数，参数为 (src, total, sent)

**返回：**
- `bool`: 成功返回 True

**抛出：**
- `InstallError`: 安装失败时抛出

**示例：**
```python
# 简单安装
await device.pm.install("app.apk")

# 带进度回调
def progress(src, total, sent):
    print(f"上传进度: {sent/total*100:.1f}%")

await device.pm.install("app.apk", progress_cb=progress)

# 强制覆盖安装并授予所有权限
await device.pm.install("app.apk", args="rg")
```

---

### uninstall

```python
async def uninstall(package_name: str) -> bool
```

卸载应用。

**等同于：** `adb uninstall package_name`

**参数：**
- `package_name` (str): 包名

**返回：**
- `bool`: 成功返回 True

**抛出：**
- `UninstallError`: 卸载失败时抛出

**示例：**
```python
await device.pm.uninstall("com.example.app")
```

---

### path

```python
async def path(package_name: str) -> str
```

获取应用的 APK 路径。

**参数：**
- `package_name` (str): 包名

**返回：**
- `str`: APK 路径

**抛出：**
- `NameError`: 包不存在时抛出

**示例：**
```python
apk_path = await device.pm.path("com.example.app")
print(f"APK 路径: {apk_path}")
```

---

### is_installed

```python
async def is_installed(package_name: str) -> bool
```

判断应用是否已安装。

**参数：**
- `package_name` (str): 包名

**返回：**
- `bool`: 已安装返回 True，否则返回 False

**示例：**
```python
if await device.pm.is_installed("com.example.app"):
    print("应用已安装")
else:
    print("应用未安装")
```

---

### clear

```python
async def clear(package_name: str)
```

清除应用的数据和缓存。

**等同于：** `adb shell pm clear package_name`

**参数：**
- `package_name` (str): 包名

**抛出：**
- `ClearError`: 清除失败时抛出

**示例：**
```python
await device.pm.clear("com.example.app")
```

---

### list_features

```python
async def list_features() -> Dict[str, Any]
```

列出 Android 功能列表。

**等同于：** `adb shell pm list features`

**返回：**
- `Dict[str, Any]`: 功能字典

**示例：**
```python
features = await device.pm.list_features()
for name, value in features.items():
    print(f"{name}: {value}")
```
