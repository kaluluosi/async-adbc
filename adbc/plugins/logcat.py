from . import Plugin


class LogcatPlugin(Plugin):
    async def logcat(self, args: str):
        cmd = ["logcat"]
        cmd.extend(args)
        return await self._device.shell_reader(cmd)
