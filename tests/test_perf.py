import asyncio
import time
import cProfile
from tests.testcase import DeviceTestCase


class TestPerf(DeviceTestCase):
    async def test_perf(self):
        pkg_name = "com.mobao.qq.release"
        pid = await self.device.get_pid_by_pkgname(pkg_name)
        while True:
            start = time.time()
            # await self.device.cpu.freqs
            # await self.device.cpu.get_pid_cpu_usage(pid)
            result = await asyncio.gather(
                self.device.cpu.get_pid_cpu_usage(pid),
                self.device.fps.stat(pkg_name),
                self.device.mem.stat(pkg_name),
                self.device.battery.stat(),
                self.device.temp.stat(),
                self.device.traffic.stat(pkg_name),
            )

            print(time.time() - start, result)
