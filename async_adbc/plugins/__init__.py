from .pm import PMPlugin
from .prop import PropPlugin
from .cpu import CPUPlugin
from .gpu import GPUPlugin
from .mem import MemPlugin
from .fps import FpsPlugin
from .utils import UtilsPlugin
from .battery import BatteryPlugin
from .am import ActivityManagerPlugin
from .temp import TempPlugin
from .traffic import TrafficPlugin
from .forward import ForwardPlugin
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
