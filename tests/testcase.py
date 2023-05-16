import unittest

from adbc.adbclient import ADBClient


class ADBClientTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.adbc = ADBClient()


class DeviceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.adbc = ADBClient()
        self.device = await self.adbc.device()
