import unittest

from adbc.adbclient import ADBClient


class ADBClientTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.adbc = ADBClient()


class DeviceTestCase(ADBClientTestCase):
    async def asyncSetUp(self):
        self.device = await self.adbc.device()
