"""Host 服务测试模块"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from async_adbc.client import ADBClient
from async_adbc.device import Device
from async_adbc.models import DeviceStatusNotification, ForwardRule


@pytest.mark.unit
class TestHostService:
    """测试 HostService 类"""

    @pytest.fixture
    def host_service(self):
        """创建 HostService 对象（使用 ADBClient）"""
        service = ADBClient()
        service.create_connection = AsyncMock()
        return service

    @pytest.fixture
    def mock_response(self):
        """Mock Response 对象"""
        response = MagicMock()

        async def mock_text():
            # 模拟 Response.text 的降级行为：直接返回内容
            return ""

        response.text = mock_text
        response.read = AsyncMock(return_value=b"")
        response.close = MagicMock()
        return response

    @pytest.fixture
    def mock_conn(self, mock_response):
        """Mock Connection 对象"""
        conn = MagicMock()
        conn.request = AsyncMock(return_value=mock_response)
        conn.request_without_check = AsyncMock(return_value=mock_response)
        conn.close = MagicMock()
        return conn

    def _setup_mock_response(self, mock_response, text_content: str):
        """设置 mock_response 让它返回指定内容"""
        async def mock_text():
            return text_content
        mock_response.text = mock_text

    @pytest.mark.asyncio
    async def test_version(self, host_service, mock_response, mock_conn):
        """测试获取 ADB Server 版本"""
        self._setup_mock_response(mock_response, "0029")
        host_service.create_connection = AsyncMock(return_value=mock_conn)
        version = await host_service.version()
        assert version == 41

    @pytest.mark.asyncio
    async def test_kill(self, host_service, mock_response, mock_conn):
        """测试杀死 ADB Server"""
        host_service.create_connection = AsyncMock(return_value=mock_conn)
        await host_service.kill()
        mock_conn.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_devices(self, host_service, mock_response, mock_conn):
        """测试获取设备列表"""
        devices_output = """List of devices attached
emulator-5554          device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64 device:emu64a transport_id:1
"""
        self._setup_mock_response(mock_response, devices_output)
        host_service.create_connection = AsyncMock(return_value=mock_conn)
        devices = await host_service.devices()
        assert len(devices) == 1
        assert devices[0].serialno == "emulator-5554"

    @pytest.mark.asyncio
    async def test_device(self, host_service, mock_response, mock_conn):
        """测试获取指定设备"""
        devices_output = """List of devices attached
emulator-5554          device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64 device:emu64a transport_id:1
"""
        self._setup_mock_response(mock_response, devices_output)
        host_service.create_connection = AsyncMock(return_value=mock_conn)
        device = await host_service.device("emulator-5554")
        assert device.serialno == "emulator-5554"

    @pytest.mark.asyncio
    async def test_remote_connect(self, host_service, mock_response, mock_conn):
        """测试远程连接设备"""
        self._setup_mock_response(mock_response, "connected to 192.168.1.100:5555")
        host_service.create_connection = AsyncMock(return_value=mock_conn)
        result = await host_service.remote_connect("192.168.1.100", 5555)
        assert result is True

    @pytest.mark.asyncio
    async def test_remote_disconnect(self, host_service, mock_response, mock_conn):
        """测试断开远程设备"""
        self._setup_mock_response(mock_response, "disconnected 192.168.1.100:5555")
        host_service.create_connection = AsyncMock(return_value=mock_conn)
        result = await host_service.remote_disconnect("192.168.1.100", 5555)
        assert "disconnected" in result

    @pytest.mark.asyncio
    async def test_forward_list(self, host_service, mock_response, mock_conn):
        """测试列出转发规则"""
        forward_output = """emulator-5554 tcp:8080 tcp:8080
"""
        self._setup_mock_response(mock_response, forward_output)
        host_service.create_connection = AsyncMock(return_value=mock_conn)
        rules = await host_service.forward_list()
        assert len(rules) == 1
        assert rules[0].serialno == "emulator-5554"
        assert rules[0].local == "tcp:8080"
