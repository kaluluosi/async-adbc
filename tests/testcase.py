import asyncio
import unittest
import socket

from async_adbc.adbclient import ADBClient

ARM_APK = "tests/assets/app-armeabi-v7a.apk"
PKG_NAME = "com.cloudmosa.helloworldapk"

UNITY_APK = "tests/assets/com.netease.poco.u3d.tutorial.apk"
UNITY_PKG_NAME = "com.NetEase"

DOCKER_HOST = "host.docker.internal"


def is_docker_android():
    # is in docker host
    try:
        docker_host = "host.docker.internal"
        socket.gethostbyname(docker_host)
        with socket.socket() as s:
            s.connect((docker_host,5555))
            return True
    except Exception:
        return False
    
IS_DOCKER_ANDROID = is_docker_android()

class ADBClientTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.adbc = ADBClient()


class DeviceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.adbc = ADBClient()
        self.device = await self.adbc.device()

    async def asyncTearDown(self):
        await asyncio.sleep(3)