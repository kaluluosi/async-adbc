"""温度插件测试模块"""
import pytest
from unittest.mock import AsyncMock

from async_adbc.plugins.temp import TempPlugin


@pytest.mark.unit
class TestTempPlugin:
    """测试 TempPlugin 类"""

    @pytest.fixture
    def temp_plugin(self, mock_device):
        """创建 TempPlugin 对象"""
        return TempPlugin(mock_device)

    @pytest.mark.asyncio
    async def test_stat_hardware_properties(self, temp_plugin, mock_device):
        """测试通过 dumpsys hardware_properties 获取温度"""
        mock_device.shell = AsyncMock(
            return_value="""CPU temperatures: [35.5, 36.0, 35.0]
GPU temperatures: [36.5]
Skin temperatures: [34.0]
Battery temperatures: [35.0]
"""
        )
        stat = await temp_plugin.stat()
        assert stat.cpu == 35.5
        assert stat.gpu == 36.5
        assert stat.skin == 34.0
        assert stat.battery == 35.0

    @pytest.mark.asyncio
    async def test_stat_fallback(self, temp_plugin, mock_device):
        """测试获取温度失败时降级"""
        mock_device.shell = AsyncMock(return_value="")
        stat = await temp_plugin.stat()
        assert stat.cpu == 0.0
        assert stat.gpu == 0.0
        assert stat.skin == 0.0
        assert stat.battery == 0.0
