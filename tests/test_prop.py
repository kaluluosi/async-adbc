import os
import unittest
from adbc.adbclient import ADBClient
from adbc.device import Device
from tests.testcase import DeviceTestCase


class TestPropPlugin(DeviceTestCase):
    async def test_get_props(self):
        props = await self.device.prop.properties
        self.assertGreater(len(props), 0)
