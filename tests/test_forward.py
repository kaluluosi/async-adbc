from tests.testcase import DeviceTestCase


class TestForwardPlugin(DeviceTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        await self.device.forward.forward_remove_all()

    async def test_forward(self):
        local = "tcp:2222"
        remote = "tcp:5555"
        await self.device.forward.forward(local, remote, True)

        forward_list = await self.device.forward.forward_list()
        self.assertGreater(len(forward_list), 0)
        for rule in forward_list:
            self.assertEqual(rule.serialno, self.device.serialno)

        rule = forward_list[0]
        self.assertEqual(rule.local, local)
        self.assertEqual(rule.remote, remote)

        await self.adbc.forward_remove(self.device.serialno, rule)
        forward_list = await self.adbc.forward_list()
        self.assertEqual(len(forward_list), 0)
