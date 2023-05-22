import asyncio
import unittest
from tests.testcase import DeviceTestCase

ARM_APK = r"tests\assets\app-armeabi-v7a.apk"
PKG_NAME = "com.cloudmosa.helloworldapk"


class TestCpuPlugin(DeviceTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        # await self.device.pm.install(ARM_APK)

    async def asyncTearDown(self):
        await super().asyncTearDown()
        # await self.device.pm.uninstall(PKG_NAME)

    async def test_cpu_count(self):
        cpu_count = await self.device.cpu.count
        self.assertGreater(cpu_count, 0)

    async def test_cpu_freqs(self):
        cpu_count = await self.device.cpu.count
        freqs = await self.device.cpu.freqs

        self.assertEqual(len(freqs), cpu_count)
        self.assertGreater(freqs[0].min, 0)
        self.assertGreater(freqs[0].cur, 0)
        self.assertGreater(freqs[0].max, 0)

    async def test_normalize_factor(self):
        factor = await self.device.cpu.normalize_factor

        self.assertGreater(factor, 0)

    async def test_cpu_stats(self):
        stat = await self.device.cpu.cpu_stats

        cpu_count = await self.device.cpu.count

        self.assertEqual(len(stat), cpu_count)

    async def test_cpu_usage(self):
        usage = await self.device.cpu.cpu_usages

        cpu_count = await self.device.cpu.count

        self.assertEqual(len(usage), cpu_count)

    async def test_total_cpu_stat(self):
        stat = await self.device.cpu.total_cpu_stat

        self.assertGreater(stat.usage, 0)

    async def test_total_cpu_usage(self):
        usage = await self.device.cpu.total_cpu_usage
        self.assertGreater(usage.usage, 0)

    async def test_pid_cpu_stat(self):
        PKG_NAME = "com.android.browser"
        await self.device.am.start_app(PKG_NAME)

        pid = await self.device.get_pid_by_pkgname(PKG_NAME)
        stat = await self.device.cpu.get_pid_cpu_stat(pid)

        self.assertGreater(stat.utime, 0)

    async def test_pid_cpu_usage(self):
        PKG_NAME = "com.android.browser"
        await self.device.am.start_app(PKG_NAME)
        pid = await self.device.get_pid_by_pkgname(PKG_NAME)
        pip_stat = await self.device.cpu.get_pid_cpu_usage(pid)

        self.assertGreaterEqual(pip_stat.usage, 0)

        total_cpu_stat = await self.device.cpu.total_cpu_usage
        self.assertGreaterEqual(total_cpu_stat.usage, pip_stat.usage)

    async def test_cpu_name(self):
        cpu_name = await self.device.cpu.cpu_name
        self.assertTrue(cpu_name)

    async def test_info(self):
        await self.device.cpu.info

    async def test_cpu(self):
        PKG_NAME = "com.android.browser"
        await self.device.am.start_app(PKG_NAME)
        pid = await self.device.get_pid_by_pkgname(PKG_NAME)

        while True:
            total, app = await asyncio.gather(
                self.device.cpu.total_cpu_usage, self.device.cpu.get_pid_cpu_usage(pid)
            )
            print("total:", total.usage, "app:", app.usage)
            print("total:", total.normalized, "app:", app.normalized)
            await asyncio.sleep(1)

        self.assertGreater(total.usage, app.usage)
