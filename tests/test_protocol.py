import unittest
from adbc.protocol import request


class ProtocalTest(unittest.IsolatedAsyncioTestCase):
    async def test_connect(self):
        conn = await request()
        resp = await conn.request("host:version")
        ret = await resp.text()
        self.assertTrue(ret)
