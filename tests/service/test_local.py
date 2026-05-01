"""Local 服务测试模块"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from async_adbc.device import Device


class TestLocalService:
    """测试 LocalService 类"""

    @pytest.fixture
    def local_service(self, mock_adbc):
        """创建 LocalService 对象（使用 Device）"""
        service = Device(mock_adbc, "emulator-5554")
        service.create_connection = AsyncMock()
        return service

    @pytest.fixture
    def mock_adbc(self):
        """Mock ADBClient"""
        from unittest.mock import MagicMock
        adbc = MagicMock()
        adbc.create_connection = AsyncMock()
        return adbc

    @pytest.fixture
    def mock_response(self):
        """Mock Response 对象"""
        response = MagicMock()

        async def mock_text():
            return ""

        response.text = mock_text
        response.read = AsyncMock(return_value=b"")
        response.reader = MagicMock()
        response.reader.read = AsyncMock(return_value=b"")
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

    def _setup_mock_response(self, mock_response, read_data: bytes):
        """设置 mock_response 让它的 read 返回指定内容"""
        mock_response.read = AsyncMock(return_value=read_data)

    @pytest.mark.asyncio
    async def test_shell(self, local_service, mock_response, mock_conn):
        """测试 shell 方法"""
        self._setup_mock_response(mock_response, b"hello world")
        local_service.create_connection = AsyncMock(return_value=mock_conn)
        result = await local_service.shell("echo hello world")
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_shell_raw(self, local_service, mock_response, mock_conn):
        """测试 shell_raw 方法"""
        self._setup_mock_response(mock_response, b"raw data")
        local_service.create_connection = AsyncMock(return_value=mock_conn)
        result = await local_service.shell_raw("echo raw data")
        assert result == b"raw data"

    @pytest.mark.asyncio
    async def test_adbd_tcpip(self, local_service, mock_response, mock_conn):
        """测试开启 TCPIP 模式"""
        self._setup_mock_response(
            mock_response,
            b"restarting in TCP mode port: 5555"
        )
        local_service.create_connection = AsyncMock(return_value=mock_conn)
        result = await local_service.adbd_tcpip(5555)
        assert "restarting in TCP mode port" in result

    @pytest.mark.asyncio
    async def test_adbd_root(self, local_service, mock_response, mock_conn):
        """测试切换到 root 模式"""
        self._setup_mock_response(mock_response, b"restarting adbd as root")
        local_service.create_connection = AsyncMock(return_value=mock_conn)
        await local_service.adbd_root()

    @pytest.mark.asyncio
    async def test_adbd_unroot(self, local_service, mock_response, mock_conn):
        """测试切换到非 root 模式"""
        self._setup_mock_response(
            mock_response,
            b"restarting adbd as non root"
        )
        local_service.create_connection = AsyncMock(return_value=mock_conn)
        await local_service.adbd_unroot()

    @pytest.mark.asyncio
    async def test_remount(self, local_service, mock_response, mock_conn):
        """测试重新挂载"""
        self._setup_mock_response(mock_response, b"remount succeeded")
        local_service.create_connection = AsyncMock(return_value=mock_conn)
        result = await local_service.remount()
        assert "remount succeeded" in result

    @pytest.mark.asyncio
    async def test_reverse_list(self, local_service, mock_response, mock_conn):
        """测试列出反向代理规则"""
        reverse_output = """tcp tcp:8080 tcp:8080
"""
        async def mock_text():
            return reverse_output

        mock_response.text = mock_text
        local_service.create_connection = AsyncMock(return_value=mock_conn)
        rules = await local_service.reverse_list()
        assert len(rules) == 1
