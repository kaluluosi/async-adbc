import typing
from . import Plugin

if typing.TYPE_CHECKING:
    from async_adbc.adbclient import ForwardRule


class ForwardPlugin(Plugin):
    """Device的forward端口映射封装

    与ADBClient的forward接口区别在于Device的forward接口都是作用在当前设备。
    可以理解为方法参数中serialno已经默认传入了Device的serialno。

    Args:
        Plugin (_type_): _description_
    """

    async def forward_list(self) -> list["ForwardRule"]:
        rules = await self._device.adbc.forward_list()
        rules: list[ForwardRule] = list(
            filter(lambda rule: rule.serialno == self._device.serialno, rules)
        )
        return rules

    async def forward(self, local: str, remote: str, norebind: bool = False):
        return await self._device.adbc.forward(
            self._device.serialno, local, remote, norebind
        )

    async def forward_remove(self, local: typing.Union[str, "ForwardRule"]):
        return await self._device.adbc.forward_remove(self._device.serialno, local)

    async def forward_remove_all(self):
        rules = await self.forward_list()
        for rule in rules:
            return await self.forward_remove(rule)
