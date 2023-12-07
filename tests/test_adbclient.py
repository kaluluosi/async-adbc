import unittest

from tests.testcase import ADBClientTestCase, IS_DOCKER_ANDROID, DOCKER_HOST
from async_adbc.exceptions import DeviceNotFoundError
from async_adbc.device import Status


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

    @unittest.skipIf(
        not IS_DOCKER_ANDROID, "这个用例只在运行了 docker android 容器的主机上执行"
    )
    async def test_remote_connect(self):
        addr = (DOCKER_HOST, 5555)
        serialno = f"{addr[0]}:{addr[1]}"
        ret = await self.adbc.remote_connect(*addr)
        self.assertTrue(ret, "连接不成功")

        device = await self.adbc.device(serialno)
        self.assertEqual(device.serialno, serialno, "序列号不一致")

        ret = await self.adbc.remote_disconnect(*addr)
        self.assertTrue(ret, "断开连接不成功")
        with self.assertRaises(DeviceNotFoundError):
            await self.adbc.device(serialno)


class TestForward(ADBClientTestCase):
    async def asyncSetUp(self):
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
