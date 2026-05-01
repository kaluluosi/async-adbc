import typing
from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from async_adbc.device import Device


class Plugin:
    def __init__(self, device: "Device"):
        self._device = device


def register_plugin(name: str, attr_name: str):
    """插件注册装饰器

    Args:
        name: 插件名称
        attr_name: Device 上的属性名
    """
    from .plugins._registry import _registry

    def decorator(cls: Type[Plugin]):
        _registry.register(name, attr_name, cls)
        return cls

    return decorator
