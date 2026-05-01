"""Host 服务集成测试模块"""
import pytest

from async_adbc.client import ADBClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestHostServiceIntegration:
    """测试 HostService 集成"""

    async def test_version(self):
        """测试获取 ADB Server 版本"""
        adbc = ADBClient()
        try:
            version = await adbc.version()
            assert isinstance(version, int)
            assert version > 0
        finally:
            adbc.close()

    async def test_devices(self):
        """测试获取设备列表"""
        adbc = ADBClient()
        try:
            devices = await adbc.devices()
            assert len(devices) >= 1
            serialnos = [d.serialno for d in devices]
            assert "emulator-5554" in serialnos
        finally:
            adbc.close()

    async def test_device(self):
        """测试获取指定设备"""
        adbc = ADBClient()
        try:
            device = await adbc.device("emulator-5554")
            assert device.serialno == "emulator-5554"
        finally:
            device.close()
            adbc.close()
