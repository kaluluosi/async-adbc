from . import Plugin


class ForwardPlugin(Plugin):
    async def forward_list(self):
        rules = await self._device.adbc.forward_list()
        return filter(lambda rule: rule.serialno == self.serialno, rules)

    async def forward(self, local: str, remote: str, norebind: bool = False):
        return await self._device.adbc.forward(self.serialno, local, remote, norebind)

    async def forward_remove(self, local: str):
        return await self._device.adbc.forward_remove(self.serialno, local)

    async def forward_remove_all(self):
        return await self._device.adbc.forward_remove_all()
