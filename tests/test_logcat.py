from tests.testcase import DeviceTestCase


class TestLogcatPlugin(DeviceTestCase):
    async def test_logcat(self):
        reader = await self.device.logcat.reader()
        counter = 0
        while counter < 5:
            counter += 1
            line = await reader.readline()
            self.assertTrue(line)

    async def test_logs(self):
        counter = 0

        async for log in self.device.logcat.logs():
            self.assertTrue(log)
            counter += 1

            if counter > 3:
                break
