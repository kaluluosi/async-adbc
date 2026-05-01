# 导入所有插件以触发注册
from . import pm
from . import prop
from . import cpu
from . import gpu
from . import mem
from . import fps
from . import battery
from . import temp
from . import traffic
from . import utils
from . import forward
from . import am
from . import logcat
from . import minicap
from . import wm
from . import input


# 重新导出插件类以保持向后兼容
from .pm import PMPlugin
from .prop import PropPlugin
from .cpu import CPUPlugin
from .gpu import GPUPlugin
from .mem import MemPlugin
from .fps import FpsPlugin
from .battery import BatteryPlugin
from .temp import TempPlugin
from .traffic import TrafficPlugin
from .utils import UtilsPlugin
from .forward import ForwardPlugin
from .am import ActivityManagerPlugin
from .logcat import LogcatPlugin
from .minicap import MinicapPlugin
from .wm import WMPlugin
from .input import InputPlugin


__all__ = [
    "PMPlugin",
    "PropPlugin",
    "CPUPlugin",
    "GPUPlugin",
    "MemPlugin",
    "FpsPlugin",
    "UtilsPlugin",
    "BatteryPlugin",
    "ActivityManagerPlugin",
    "TempPlugin",
    "TrafficPlugin",
    "ForwardPlugin",
    "LogcatPlugin",
    "MinicapPlugin",
    "WMPlugin",
    "InputPlugin",
]
