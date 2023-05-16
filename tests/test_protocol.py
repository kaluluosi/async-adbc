import unittest
from async_adbc.protocol import create_connection


class ProtocalTest(unittest.IsolatedAsyncioTestCase):
    async def test_connect(self):
        conn = await create_connection()
        resp = await conn.request("host:version")
        ret = await resp.text()
        self.assertTrue(ret)
