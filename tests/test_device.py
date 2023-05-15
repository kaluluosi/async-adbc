import os
import unittest
import tempfile
from adbc.adbclient import ADBClient
from tests.testcase import DeviceTestCase


class TestDevice(DeviceTestCase):
    def setUp(self) -> None:
        self.adbc = ADBClient()

    async def asyncSetUp(self) -> None:
        self.device = await self.adbc.device()
        await self.device.reverse_remove_all()

    async def asyncTearDown(self):
        await self.device.reverse_remove_all()

    async def test_shell(self):
        ret = await self.device.shell("echo", "hello")
        self.assertEqual(ret, "hello")

    async def test_shell_row(self):
        ret = await self.device.shell_raw("echo", "hello")
        self.assertEqual(ret, b"hello\n")

    async def test_shell_reader(self):
        ret = await self.device.shell_reader("echo", "hello\n", "echo", "shit\n")
        lines = []
        while line := await ret.readline():
            lines.append(line)

        self.assertEqual(len(lines), 2)
        self.assertEqual(lines, [b"hello\n", b"shit\n"])

    async def test_tcpip(self):
        ret = await self.device.adbd_tcpip(5555)
        self.assertEqual(ret, "restarting in TCP mode port: 5555")

    @unittest.skip(reason="非root设备一定失败")
    async def test_root(self):
        ret = await self.device.adbd_root()
        self.assertEqual(ret, "restarting in root mode")

    async def test_reboot(self):
        """没抛异常就算成功"""
        await self.device.reboot()

    @unittest.skip(reason="非root设备一定失败")
    async def test_remount(self):
        await self.device.remount()

    async def test_push_pull(self):
        await self.device.push("tests/assets/push.txt", "/sdcard/push.txt")

        ls = await self.device.shell("ls", "/sdcard/")
        self.assertTrue("push.txt" in ls)

        with tempfile.TemporaryDirectory() as dir:
            push_txt = os.path.join(dir, "push_txt")
            await self.device.pull("/sdcard/push.txt", push_txt)

            self.assertTrue(os.path.exists(push_txt))

            with open(push_txt) as f:
                txt = f.read()
                self.assertEqual("Test Push", txt)

    async def test_reverse(self):
        """测完所有reverse的指令"""
        rules = await self.device.reverse_list()

        self.assertEqual(len(rules), 0)

        await self.device.reverse("tcp:5555", "tcp:2222")

        rules = await self.device.reverse_list()

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].local, "tcp:2222")

        await self.device.reverse_remove(rules[0])
        rules = await self.device.reverse_list()

        self.assertFalse(rules)
