# 插件列表

async-adbc 提供了丰富的插件来封装各种 Android 设备操作功能。

## 插件概览

| 插件 | 属性名 | 说明 |
|------|--------|------|
| [AMPlugin](./am.md) | `device.am` | Activity Manager，应用启动和停止 |
| [BatteryPlugin](./battery.md) | `device.battery` | 电池信息 |
| [CPUPlugin](./cpu.md) | `device.cpu` | CPU 信息和占用率 |
| [ForwardPlugin](./forward.md) | `device.forward` | 端口转发 |
| [FpsPlugin](./fps.md) | `device.fps` | 帧率统计 |
| [GPUPlugin](./gpu.md) | `device.gpu` | GPU 信息 |
| [InputPlugin](./input.md) | `device.input` | 输入模拟（点击、滑动、按键等） |
| [LogcatPlugin](./logcat.md) | `device.logcat` | 日志 |
| [MemPlugin](./mem.md) | `device.mem` | 内存信息 |
| [MiniCapPlugin](./minicap.md) | `device.minicap` | 截图（高效） |
| [PMPlugin](./pm.md) | `device.pm` | 包管理（安装、卸载、列出包等） |
| [PropPlugin](./prop.md) | `device.prop` | 属性（获取设备属性） |
| [TempPlugin](./temp.md) | `device.temp` | 温度 |
| [TrafficPlugin](./traffic.md) | `device.traffic` | 流量统计 |
| [UtilsPlugin](./utils.md) | `device.utils` | 工具方法 |
| [WMPlugin](./wm.md) | `device.wm` | 窗口管理（分辨率、方向） |
| [ScrcpyPlugin](./scrcpy.md) | `device.scrcpy` | Scrcpy 屏幕镜像和控制 |

## 基本使用

所有插件都通过 `Device` 对象的属性访问：

```python
from async_adbc import ADBClient

async def main():
    adbc = ADBClient()
    device = await adbc.device()
    
    # 使用 PM 插件
    packages = await device.pm.list_packages()
    
    # 使用 CPU 插件
    cpu_usage = await device.cpu.get_total_cpu_usage()
    
    # 使用 Input 插件
    await device.input.tap(500, 500)

asyncio.run(main())
```
