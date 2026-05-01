from dataclasses import dataclass
from typing import List, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from async_adbc.plugin import Plugin


@dataclass
class PluginMetadata:
    name: str
    attr_name: str
    plugin_class: Type["Plugin"]
    enabled: bool = True


class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, PluginMetadata] = {}

    def register(self, name: str, attr_name: str, plugin_class: Type["Plugin"]):
        self._plugins[name] = PluginMetadata(
            name=name,
            attr_name=attr_name,
            plugin_class=plugin_class,
        )

    def get_all(self) -> List[PluginMetadata]:
        return [p for p in self._plugins.values() if p.enabled]

    def get(self, name: str) -> PluginMetadata:
        return self._plugins[name]


_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    return _registry
