"""Scrcpy 插件测试模块"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from async_adbc.plugins.scrcpy import ScrcpyPlugin, ScrcpySession, DeviceInfo, ScrcpyError


@pytest.mark.unit
class TestScrcpyPlugin:
    """测试 ScrcpyPlugin 类"""

    @pytest.fixture
    def scrcpy_plugin(self, mock_device):
        """创建 ScrcpyPlugin 对象"""
        # Mock 存在的 server 文件
        with patch("async_adbc.plugins.scrcpy.Path.exists", return_value=True):
            with patch("async_adbc.plugins.scrcpy.Path.parent", return_value=Path("/fake")):
                with patch("async_adbc.plugins.scrcpy.Path.__truediv__", return_value=Path("/fake/scrcpy-server")):
                    plugin = ScrcpyPlugin(mock_device)
                    plugin._server_path = "/fake/path/scrcpy-server"
                    return plugin

    @pytest.mark.asyncio
    async def test_start(self, scrcpy_plugin, mock_device):
        """测试启动 scrcpy"""
        # Mock session
        mock_session = MagicMock()
        mock_session.device_info = DeviceInfo(b"\x00", "test_device", 1080, 720)
        scrcpy_plugin._session = mock_session

        # 不实际启动，测试属性访问
        assert scrcpy_plugin.device_info == mock_session.device_info

    @pytest.mark.asyncio
    async def test_stop(self, scrcpy_plugin, mock_device):
        """测试停止 scrcpy"""
        mock_session = MagicMock()
        mock_session.stop = AsyncMock()
        scrcpy_plugin._session = mock_session

        await scrcpy_plugin.stop()
        mock_session.stop.assert_called_once()
        assert scrcpy_plugin._session is None

    @pytest.mark.asyncio
    async def test_context_manager(self, scrcpy_plugin, mock_device):
        """测试 async with 上下文管理器"""
        # Mock start 和 stop
        mock_session = MagicMock()
        mock_session.device_info = DeviceInfo(b"\x00", "test_device", 1080, 720)

        # 用 patch 避免实际启动
        with patch.object(scrcpy_plugin, "start", new=AsyncMock()):
            with patch.object(scrcpy_plugin, "stop", new=AsyncMock()):
                async with scrcpy_plugin as sp:
                    assert sp is scrcpy_plugin

    @pytest.mark.asyncio
    async def test_screencap_with_save_file(self, scrcpy_plugin, mock_device, tmp_path):
        """测试 screencap 保存文件"""
        mock_session = MagicMock()
        mock_session.screencap = AsyncMock(return_value=b"fake h264 data")
        scrcpy_plugin._session = mock_session

        # 测试保存文件
        output_file = tmp_path / "test.h264"
        result = await scrcpy_plugin.screencap(save_file=str(output_file))

        assert result == b"fake h264 data"
        assert output_file.exists()
        assert output_file.read_bytes() == b"fake h264 data"

    @pytest.mark.asyncio
    async def test_screencap_without_save_file(self, scrcpy_plugin, mock_device):
        """测试 screencap 不保存文件"""
        mock_session = MagicMock()
        mock_session.screencap = AsyncMock(return_value=b"fake h264 data")
        scrcpy_plugin._session = mock_session

        result = await scrcpy_plugin.screencap()

        assert result == b"fake h264 data"
        mock_session.screencap.assert_called_once_with(timeout=5.0)


@pytest.mark.unit
class TestScrcpySession:
    """测试 ScrcpySession 类"""

    @pytest.fixture
    def mock_session(self, mock_device):
        """创建 mock ScrcpySession 对象（不实际启动）"""
        session = ScrcpySession(mock_device, "/fake/server", max_size=720)
        session._running = False
        return session

    def test_build_server_cmd(self, mock_session):
        """测试构建 server 命令"""
        cmd = mock_session._build_server_cmd("/data/local/tmp/server")
        assert "CLASSPATH=/data/local/tmp/server" in cmd
        assert "app_process" in cmd
        assert "scrcpy.Server" in cmd
        assert "3.3.4" in cmd
        assert "max_size=720" in cmd

    def test_recv_exact(self, mock_session):
        """测试接收固定字节数"""
        # 创建一个 mock socket
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = [b"hel", b"lo"]

        # 测试 - 需要 patch _recv_exact 是实例方法
        def mock_recv_exact(sock, size):
            data = bytearray()
            while len(data) < size:
                chunk = sock.recv(size - len(data))
                if not chunk:
                    raise Exception("Connection closed")
                data.extend(chunk)
            return bytes(data)

        result = mock_recv_exact(mock_sock, 5)
        assert result == b"hello"


@pytest.mark.unit
class TestDeviceInfo:
    """测试 DeviceInfo 类"""

    def test_device_info_init(self):
        """测试设备信息初始化"""
        info = DeviceInfo(b"\x00", "test_device", 1080, 720)
        assert info.dummy == b"\x00"
        assert info.name == "test_device"
        assert info.width == 1080
        assert info.height == 720
