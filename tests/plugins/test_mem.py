"""内存插件测试模块"""
import pytest
from unittest.mock import AsyncMock

from async_adbc.plugins.mem import MemPlugin


@pytest.mark.unit
class TestMemPlugin:
    """测试 MemPlugin 类"""

    @pytest.fixture
    def mem_plugin(self, mock_device):
        """创建 MemPlugin 对象"""
        return MemPlugin(mock_device)

    @pytest.mark.asyncio
    async def test_get_info(self, mem_plugin, mock_device, sample_meminfo_output):
        """测试获取内存信息"""
        async def mock_shell(cmd):
            if "/proc/meminfo" in cmd:
                return sample_meminfo_output
            return ""
        mock_device.shell = mock_shell
        info = await mem_plugin.get_info()
        assert info.mem_total == 5872084
        assert info.swap_total == 1234567

    @pytest.mark.asyncio
    async def test_get_info_fallback(self, mem_plugin, mock_device):
        """测试获取内存信息失败时降级"""
        mock_device.shell = AsyncMock(return_value="")
        info = await mem_plugin.get_info()
        assert info.mem_total == 0
        assert info.swap_total == 0

    @pytest.mark.asyncio
    async def test_stat(self, mem_plugin, mock_device, sample_dumpsys_meminfo_output):
        """测试获取应用内存统计"""
        mock_device.shell = AsyncMock(return_value=sample_dumpsys_meminfo_output)
        stat = await mem_plugin.stat("com.test.app")
        assert stat.pss == 8234
        assert stat.private_dirty == 5298
        assert stat.heap_size == 7900
        assert stat.heap_alloc == 4567
        assert stat.heap_free == 3333

    @pytest.mark.asyncio
    async def test_stat_fallback(self, mem_plugin, mock_device):
        """测试获取应用内存统计失败时降级"""
        mock_device.shell = AsyncMock(return_value="")
        stat = await mem_plugin.stat("com.test.app")
        assert stat.pss == 0
