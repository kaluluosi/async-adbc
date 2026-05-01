import pytest
from unittest.mock import AsyncMock

from async_adbc.plugins.pm import PMPlugin


class TestPMPlugin:
    @pytest.fixture
    def pm_plugin(self, mock_device):
        return PMPlugin(mock_device)

    @pytest.mark.asyncio
    async def test_list_packages(self, pm_plugin, mock_device):
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
        mock_device.shell = AsyncMock(
            return_value="package:/data/app/com.test.app/base.apk"
        )
        result = await pm_plugin.is_installed("com.test.app")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_installed_false(self, pm_plugin, mock_device):
        mock_device.shell = AsyncMock(return_value="")
        result = await pm_plugin.is_installed("com.nonexistent.app")
        assert result is False

    @pytest.mark.asyncio
    async def test_path(self, pm_plugin, mock_device):
        mock_device.shell = AsyncMock(
            return_value="package:/data/app/com.test.app/base.apk"
        )
        path = await pm_plugin.path("com.test.app")
        assert path == "/data/app/com.test.app/base.apk"

    @pytest.mark.asyncio
    async def test_install_success(self, pm_plugin, mock_device, tmp_path):
        apk_file = tmp_path / "test.apk"
        apk_file.write_bytes(b"fake apk")
        mock_device.push = AsyncMock()
        mock_device.shell = AsyncMock(return_value="Success\n")
        result = await pm_plugin.install(str(apk_file))
        assert result is True

    @pytest.mark.asyncio
    async def test_uninstall_success(self, pm_plugin, mock_device):
        mock_device.shell = AsyncMock(return_value="Success\n")
        result = await pm_plugin.uninstall("com.test.app")
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_success(self, pm_plugin, mock_device):
        mock_device.shell = AsyncMock(return_value="Success\n")
        await pm_plugin.clear("com.test.app")

    @pytest.mark.asyncio
    async def test_list_features(self, pm_plugin, mock_device):
        mock_device.shell = AsyncMock(
            return_value="""feature:reqGlEsVersion=0x30000
feature:android.hardware.camera
feature:android.hardware.wifi
"""
        )
        features = await pm_plugin.list_features()
        assert "android.hardware.camera" in features
        assert features["reqGlEsVersion"] == "0x30000"
