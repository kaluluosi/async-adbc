import typing

if typing.TYPE_CHECKING:
    from async_adbc.device import Device


class Plugin:
    def __init__(self, device: "Device") -> None:
        self._device = device


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
