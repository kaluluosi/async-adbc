# InputPlugin

输入模拟插件，用于模拟点击、滑动、按键等操作。

**访问方式：** `device.input`

---

## 方法

### text

```python
async def text(text: str)
```

输入文本。

**参数：**
- `text` (str): 要输入的文本

**示例：**
```python
await device.input.text("Hello World!")
```

---

### keyevent

```python
async def keyevent(key: Union[int, str], long_press: bool = False)
```

按键事件。

按键码和按键名参考 [Android KeyEvent](https://developer.android.com/reference/android/view/KeyEvent)。

**参数：**
- `key` (Union[int, str]): 按键码或按键名
- `long_press` (bool): 是否长按

**常用按键名：**
- `KEYCODE_HOME`: Home 键
- `KEYCODE_BACK`: 返回键
- `KEYCODE_MENU`: 菜单键
- `KEYCODE_POWER`: 电源键
- `KEYCODE_VOLUME_UP`: 音量加
- `KEYCODE_VOLUME_DOWN`: 音量减

**示例：**
```python
# 点击 Home 键
await device.input.keyevent("KEYCODE_HOME")

# 点击返回键（使用按键码）
await device.input.keyevent(4)

# 长按电源键
await device.input.keyevent("KEYCODE_POWER", long_press=True)
```

---

### tap

```python
async def tap(x: int, y: int)
```

点击屏幕。

**参数：**
- `x` (int): X 坐标
- `y` (int): Y 坐标

**示例：**
```python
await device.input.tap(500, 500)
```

---

### swipe

```python
async def swipe(x1: int, y1: int, x2: int, y2: int, duration: Optional[int] = None)
```

滑动。

**参数：**
- `x1` (int): 起始 X 坐标
- `y1` (int): 起始 Y 坐标
- `x2` (int): 结束 X 坐标
- `y2` (int): 结束 Y 坐标
- `duration` (int, optional): 滑动时长（毫秒）

**示例：**
```python
# 从左向右滑动
await device.input.swipe(100, 500, 500, 500)

# 慢速滑动
await device.input.swipe(100, 500, 500, 500, duration=1000)
```

---

### drag_and_drop

```python
async def drag_and_drop(x1: int, y1: int, x2: int, y2: int, duration: Optional[int] = None)
```

拖拽。

**参数：**
- `x1` (int): 起始 X 坐标
- `y1` (int): 起始 Y 坐标
- `x2` (int): 结束 X 坐标
- `y2` (int): 结束 Y 坐标
- `duration` (int, optional): 拖拽时长（毫秒）

**示例：**
```python
await device.input.drag_and_drop(100, 500, 500, 500)
```

---

### press

```python
async def press()
```

轨迹球点击。

与 `tap` 不同的地方是，`press` 要搭配 `roll` 使用。通过 `roll` 将鼠标移动到某个坐标，然后 `press` 按下轨迹球点击。

**示例：**
```python
await device.input.roll(100, 100)
await device.input.press()
```

---

### roll

```python
async def roll(x: int, y: int)
```

移动轨迹球。

**参数：**
- `x` (int): X 偏移
- `y` (int): Y 偏移

**示例：**
```python
await device.input.roll(10, 10)
```

---

### event

```python
async def event(event_type: Literal["DOWN", "UP", "MOVE"], x: int, y: int)
```

原始的移动按下弹起触摸事件。

这个方法公开的目的是方便用户去自己实现一些复杂的操作，比如签名、画图、组合手势。

**参数：**
- `event_type` (Literal["DOWN", "UP", "MOVE"]): 事件类型
- `x` (int): X 坐标
- `y` (int): Y 坐标

**示例：**
```python
# 模拟点击：DOWN -> MOVE -> UP
await device.input.event("DOWN", 500, 500)
await device.input.event("MOVE", 500, 500)
await device.input.event("UP", 500, 500)
```
