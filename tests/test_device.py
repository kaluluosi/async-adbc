import asyncio
import os
import tempfile
import unittest
from tests.testcase import DeviceTestCase,ARM_APK,PKG_NAME


class TestDevice(DeviceTestCase):
        
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        await self.device.reverse_remove_all()

    async def asyncTearDown(self):
        try:
            await self.device.reverse_remove_all()
        except Exception:
            pass

    async def test_shell(self):
        ret = await self.device.shell("echo", "hello")
        self.assertEqual(ret, "hello")

    async def test_shell_row(self):
        ret = await self.device.shell_raw("echo", "hello")
        ret = ret.decode().strip()
        self.assertEqual(ret, "hello")

    async def test_shell_reader(self):
        ret = await self.device.shell_reader("echo", "hello\n", "echo", "shit\n")
        lines = []
        while line := await ret.readline():
            lines.append(line)

        self.assertEqual(len(lines), 2)

    @unittest.skip("这个命令会重启adbd,会导致其他用例失败")
    async def test_tcpip(self):
        ret = await self.device.adbd_tcpip(5555)
        self.assertTrue("restarting in TCP mode port" in ret)


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
        rules = await self.device.reverse_list()

        self.assertEqual(len(rules), 0)

        await self.device.reverse("tcp:5555", "tcp:2222")

        rules = await self.device.reverse_list()

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].local, "tcp:2222")

        await self.device.reverse_remove(rules[0])
        rules = await self.device.reverse_list()

        self.assertFalse(rules)

    async def test_get_pid_by_pkgname(self):
        
        await self.device.pm.install(ARM_APK)
        await asyncio.sleep(1)
        await self.device.am.start_app(PKG_NAME)
        await asyncio.sleep(1)
        
        pid = await self.device.get_pid_by_pkgname(PKG_NAME)

        self.assertTrue(pid)
        
        await self.device.pm.uninstall(PKG_NAME)
        

class TestRoot(DeviceTestCase):
    @unittest.skip("这个命令会重启adbd,会导致其他用例失败")
    async def test_root(self):
        ret = await self.device.adbd_root()
        self.assertEqual(ret, True)
    
    @unittest.skip("这个命令会重启adbd,会导致其他用例失败")
    async def test_unroot(self):
        ret = await self.device.adbd_unroot()
        self.assertEqual(ret, True)


class TestReboot(DeviceTestCase):
    
    @unittest.skip("这个命令会重启adbd,会导致其他用例失败")
    async def test_reboot(self):
        await self.device.reboot()

    @unittest.skip("这个命令会重启adbd,会导致其他用例失败")
    async def test_remount(self):
        await self.device.adbd_root()
        await self.device.remount()