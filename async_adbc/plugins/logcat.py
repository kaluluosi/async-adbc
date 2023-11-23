from asyncio import StreamReader
from typing import Any, AsyncGenerator
from async_adbc.plugin import Plugin


class LogcatPlugin(Plugin):
    async def reader(self, *args: str) -> StreamReader:
        """返回logcat的reader，自行通过readline读取下一行

        WARNING: reader用完需要手动关闭

        Returns:
            StreamReader: 读取器
        """
        reader = await self._device.shell_reader("logcat", *args)
        return reader

    async def logs(self, *args: str) -> AsyncGenerator[Any, str]:
        """将reader封装成一个异步迭代器，你可以通过async for迭代每一行

        Returns:
            AsyncGenerator[Any, str]: _description_

        Yields:
            Iterator[AsyncGenerator[Any, str]]: _description_
        """
        reader = await self.reader()
        while not reader.at_eof():
            line = await reader.readline()
            yield line
