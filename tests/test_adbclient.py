import unittest

from typing import Any, Coroutine
from tests.testcase import ADBClientTestCase, DeviceTestCase
from adbc.adbclient import ADBClient, ADBClient, DeviceNotFoundError
from adbc.device import Status


class TestAsyncADBClient(ADBClientTestCase):
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
            await self.adbc.device(f"192.168.1.5:{addr[1]}")


class TestForward(ADBClientTestCase):
    async def asyncSetUp(self) -> Coroutine[Any, Any, None]:
        await self.adbc.forward_remove_all()

    async def test_forward(self):
        device = await self.adbc.device()
        local = "tcp:2222"
        remote = "tcp:5555"
        await self.adbc.forward(device.serialno, local, remote, True)

        forward_list = await self.adbc.forward_list()
        self.assertGreater(len(forward_list), 0)

        rule = forward_list[0]
        self.assertEqual(rule.local, local)
        self.assertEqual(rule.remote, remote)

        await self.adbc.forward_remove(device.serialno, rule)
        forward_list = await self.adbc.forward_list()
        self.assertEqual(len(forward_list), 0)

    async def test_forward_remove(self):
        local = "tcp:2222"
        remote = "tcp:7555"
        device = await self.adbc.device("127.0.0.1:7555")
        await self.adbc.forward(device.serialno, local, remote)
        forward_list = await self.adbc.forward_list()

        self.assertEqual(len(forward_list), 1)
        self.assertEqual(forward_list[0].local, local)

        await self.adbc.forward_remove(device.serialno, forward_list[0])

        forward_list = await self.adbc.forward_list()
        self.assertEqual(len(forward_list), 0)
