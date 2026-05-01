"""CPU 插件测试模块"""
import pytest
from unittest.mock import AsyncMock

from async_adbc.plugins.cpu import CPUPlugin


class TestCPUPlugin:
    """测试 CPUPlugin 类"""

    @pytest.fixture
    def cpu_plugin(self, mock_device):
        """创建 CPUPlugin 对象"""
        return CPUPlugin(mock_device)

    @pytest.mark.asyncio
    async def test_get_count_sysfs(self, cpu_plugin, mock_device):
        """测试通过 sysfs 获取 CPU 核心数"""
        mock_device.shell = AsyncMock(
            return_value="""drwxr-xr-x  2 root root 0 2024-01-01 00:00 cpu0
drwxr-xr-x  2 root root 0 2024-01-01 00:00 cpu1
drwxr-xr-x  2 root root 0 2024-01-01 00:00 cpu2
drwxr-xr-x  2 root root 0 2024-01-01 00:00 cpu3
"""
        )
        count = await cpu_plugin.get_count()
        assert count == 4

    @pytest.mark.asyncio
    async def test_get_freqs_success(self, cpu_plugin, mock_device):
        """测试获取 CPU 频率成功"""
        async def mock_shell(cmd):
            if "cpuinfo_min_freq" in cmd:
                return "1000000"
            elif "scaling_cur_freq" in cmd:
                return "2000000"
            elif "cpuinfo_max_freq" in cmd:
                return "3000000"
            else:
                return ""
        mock_device.shell = mock_shell
        cpu_plugin.get_count = AsyncMock(return_value=4)
        freqs = await cpu_plugin.get_freqs()
        assert len(freqs) == 4
        assert freqs[0].min == 1000000
        assert freqs[0].max == 3000000

    @pytest.mark.asyncio
    async def test_get_freqs_fallback(self, cpu_plugin, mock_device):
        """测试获取 CPU 频率失败时降级"""
        mock_device.shell = AsyncMock(side_effect=Exception("failed"))
        cpu_plugin.get_count = AsyncMock(return_value=4)
        freqs = await cpu_plugin.get_freqs()
        assert len(freqs) == 4
        assert freqs[0].min == 1
        assert freqs[0].cur == 1
        assert freqs[0].max == 1

    @pytest.mark.asyncio
    async def test_get_cpu_stats(self, cpu_plugin, mock_device, sample_proc_stat_output):
        """测试获取 CPU 统计数据"""
        mock_device.shell = AsyncMock(return_value=sample_proc_stat_output)
        stats = await cpu_plugin.get_cpu_stats()
        assert len(stats) == 4

    @pytest.mark.asyncio
    async def test_get_total_cpu_stat(self, cpu_plugin, mock_device, sample_proc_stat_output):
        """测试获取总 CPU 统计数据"""
        mock_device.shell = AsyncMock(return_value=sample_proc_stat_output)
        stat = await cpu_plugin.get_total_cpu_stat()
        assert stat.user == 4321
        assert stat.idle == 89012

    @pytest.mark.asyncio
    async def test_get_cpu_name(self, cpu_plugin, mock_device, sample_cpuinfo_output):
        """测试获取 CPU 名称"""
        mock_device.shell = AsyncMock(return_value=sample_cpuinfo_output)
        name = await cpu_plugin.get_cpu_name()
        assert "Qualcomm" in name

    @pytest.mark.asyncio
    async def test_get_cpu_name_fallback(self, cpu_plugin, mock_device):
        """测试获取 CPU 名称失败时降级"""
        mock_device.shell = AsyncMock(side_effect=Exception("failed"))
        name = await cpu_plugin.get_cpu_name()
        assert name == "Unknown"

    @pytest.mark.asyncio
    async def test_get_pid_cpu_stat(self, cpu_plugin, mock_device):
        """测试获取进程 CPU 统计数据"""
        mock_device.shell = AsyncMock(return_value="1234 (test) R 5678 1234 ...")
        stat = await cpu_plugin.get_pid_cpu_stat(1234)
        assert stat.name == "test"

    @pytest.mark.asyncio
    async def test_get_pid_cpu_stat_not_found(self, cpu_plugin, mock_device):
        """测试获取进程 CPU 统计数据失败时降级"""
        mock_device.shell = AsyncMock(return_value="No such file or directory")
        stat = await cpu_plugin.get_pid_cpu_stat(99999)
        assert stat.name == ""
