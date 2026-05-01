"""PM 插件测试模块"""
import pytest
from unittest.mock import AsyncMock

from async_adbc.plugins.pm import PMPlugin


class TestPMPlugin:
    """测试 PMPlugin 类"""

    @pytest.fixture
    def pm_plugin(self, mock_device):
        """创建 PMPlugin 对象"""
        return PMPlugin(mock_device)

    @pytest.mark.asyncio
    async def test_list_packages(self, pm_plugin, mock_device):
        """测试列出已安装的包"""
        mock_device.shell = AsyncMock(
            return_value="""package:com.android.settings
package:com.android.systemui
package:com.test.app
"""
        )
        packages = await pm_plugin.list_packages()
        assert len(packages) == 3
        assert "com.android.settings" in packages
        assert "com.test.app" in packages

    @pytest.mark.asyncio
    async def test_is_installed_true(self, pm_plugin, mock_device):
        """测试判断已安装的包"""
        mock_device.shell = AsyncMock(
            return_value="package:/data/app/com.test.app/base.apk"
        )
        result = await pm_plugin.is_installed("com.test.app")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_installed_false(self, pm_plugin, mock_device):
        """测试判断未安装的包"""
        mock_device.shell = AsyncMock(return_value="")
        result = await pm_plugin.is_installed("com.nonexistent.app")
        assert result is False

    @pytest.mark.asyncio
    async def test_path(self, pm_plugin, mock_device):
        """测试获取包的路径"""
        mock_device.shell = AsyncMock(
            return_value="package:/data/app/com.test.app/base.apk"
        )
        path = await pm_plugin.path("com.test.app")
        assert path == "/data/app/com.test.app/base.apk"

    @pytest.mark.asyncio
    async def test_install_success(self, pm_plugin, mock_device, tmp_path):
        """测试安装成功"""
        apk_file = tmp_path / "test.apk"
        apk_file.write_bytes(b"fake apk")
        mock_device.push = AsyncMock()
        mock_device.shell = AsyncMock(return_value="Success\n")
        result = await pm_plugin.install(str(apk_file))
        assert result is True

    @pytest.mark.asyncio
    async def test_uninstall_success(self, pm_plugin, mock_device):
        """测试卸载成功"""
        mock_device.shell = AsyncMock(return_value="Success\n")
        result = await pm_plugin.uninstall("com.test.app")
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_success(self, pm_plugin, mock_device):
        """测试清除数据成功"""
        mock_device.shell = AsyncMock(return_value="Success\n")
        await pm_plugin.clear("com.test.app")

    @pytest.mark.asyncio
    async def test_list_features(self, pm_plugin, mock_device):
        """测试列出功能"""
        mock_device.shell = AsyncMock(
            return_value="""feature:reqGlEsVersion=0x30000
feature:android.hardware.camera
feature:android.hardware.wifi
"""
        )
        features = await pm_plugin.list_features()
        assert "android.hardware.camera" in features
        assert features["reqGlEsVersion"] == "0x30000"
