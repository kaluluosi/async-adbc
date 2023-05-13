import unittest

from adbc.adbclient import ADBClient, ADBClient, DeviceNotFoundError
from adbc.device import Status


class TestAsyncADBClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.adbc = ADBClient()

    async def test_version(self):
        version = await self.adbc.version()
        self.assertGreater(version, 10)

    async def test_devices(self):
        devices = await self.adbc.devices()
        self.assertGreater(len(devices), 0)

    async def test_devices_track(self):
        async for data in self.adbc.devices_track():
            self.assertTrue(data.status, Status.DEVICE)
            break

    @unittest.skip("")
    async def test_remote_connect(self):
        addr = ("192.168.1.5", 5555)
        ret = await self.adbc.remote_connect(*addr)
        devcie = await self.adbc.device(f"192.168.1.5:{addr[1]}")
        ret = await self.adbc.remote_disconnect(*addr)
        with self.assertRaises(DeviceNotFoundError):
            devcie = await self.adbc.device(f"192.168.1.5:{addr[1]}")
