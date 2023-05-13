import typing
import abc

if typing.TYPE_CHECKING:
    from ..device import Device


class PMMixin(abc.ABC):
    async def list_packages(self: "Device"):
        pass
