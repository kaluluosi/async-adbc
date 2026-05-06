"""Host 服务集成测试模块"""
import pytest

from async_adbc.client import ADBClient


@pytest.fixture
def target_serialno(device_serialno):
    """获取目标设备序列号"""
    return device_serialno


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

    async def test_devices(self, target_serialno):
        """测试获取设备列表"""
        adbc = ADBClient()
        try:
            devices = await adbc.devices()
            assert len(devices) >= 1
            
            # 如果指定了设备序列号，检查该设备是否存在
            if target_serialno:
                serialnos = [d.serialno for d in devices]
                assert target_serialno in serialnos, f"设备 {target_serialno} 不在设备列表中: {serialnos}"
        finally:
            adbc.close()

    async def test_device(self, target_serialno):
        """测试获取指定设备"""
        adbc = ADBClient()
        device = None
        try:
            device = await adbc.device(target_serialno)
            if target_serialno:
                assert device.serialno == target_serialno
        finally:
            if device:
                device.close()
            adbc.close()
