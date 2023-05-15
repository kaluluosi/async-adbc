import typing

if typing.TYPE_CHECKING:
    from adbc.device import Device


class Plugin:
    def __init__(self, device: "Device") -> None:
        self._device = device


from .pm import PMPlugin
from .prop import PropPlugin
from .cpu import CPUPlugin
from .gpu import GPUPlugin
from .utils import UtilsPlugin
