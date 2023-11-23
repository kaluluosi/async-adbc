from typing import List, TYPE_CHECKING, Union
from async_adbc.plugin import Plugin

if TYPE_CHECKING:
    from async_adbc.service.host import ForwardRule


class ForwardPlugin(Plugin):
    """Device的forward端口映射封装

    与ADBClient的forward方法区别在于Device的forward方法都是作用在当前设备。
    可以理解为方法参数中serialno已经默认传入了Device的serialno。

    Args:
        Plugin (_type_): _description_
    """

    async def forward_list(self) -> List["ForwardRule"]:
        rules = await self._device.adbc.forward_list()
        rules: List[ForwardRule] = list(
            filter(lambda rule: rule.serialno == self._device.serialno, rules)
        )
        return rules

    async def forward(self, local: str, remote: str, norebind: bool = False):
        return await self._device.adbc.forward(
            self._device.serialno, local, remote, norebind
        )

    async def forward_remove(self, local: Union[str, "ForwardRule"]):
        return await self._device.adbc.forward_remove(self._device.serialno, local)

    async def forward_remove_all(self):
        rules = await self.forward_list()
        for rule in rules:
            return await self.forward_remove(rule)
