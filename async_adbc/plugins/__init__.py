# 导入所有插件以触发注册
from . import pm  # noqa: F401
from . import prop  # noqa: F401
from . import cpu  # noqa: F401
from . import gpu  # noqa: F401
from . import mem  # noqa: F401
from . import fps  # noqa: F401
from . import battery  # noqa: F401
from . import temp  # noqa: F401
from . import traffic  # noqa: F401
from . import utils  # noqa: F401
from . import forward  # noqa: F401
from . import am  # noqa: F401
from . import logcat  # noqa: F401
from . import wm  # noqa: F401
from . import input  # noqa: F401
from . import scrcpy  # noqa: F401


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
from .wm import WMPlugin
from .input import InputPlugin
from .scrcpy import ScrcpyPlugin, ScrcpySession, DeviceInfo, ScrcpyError


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
    "WMPlugin",
    "InputPlugin",
    "ScrcpyPlugin",
    "ScrcpySession",
    "DeviceInfo",
    "ScrcpyError",
]
