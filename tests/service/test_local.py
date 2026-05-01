"""Local 服务测试模块"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from async_adbc.service.local import LocalService


class TestLocalService:
    """测试 LocalService 类"""

    @pytest.fixture
    def local_service(self):
        """创建 LocalService 对象"""
        service = LocalService()
        service.create_connection = AsyncMock()
        return service

    @pytest.fixture
    def mock_response(self):
        """Mock Response 对象"""
        response = MagicMock()
        response.text = AsyncMock(return_value="")
        response.read = AsyncMock(return_value=b"")
        response.reader = MagicMock()
        response.reader.read = AsyncMock(return_value=b"")
        response.close = MagicMock()
        return response

    @pytest.mark.asyncio
    async def test_shell(self, local_service, mock_response):
        """测试 shell 方法"""
        mock_response.reader.read = AsyncMock(return_value=b"hello world")
        local_service.request = AsyncMock(return_value=mock_response)
        result = await local_service.shell("echo hello world")
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_shell_raw(self, local_service, mock_response):
        """测试 shell_raw 方法"""
        mock_response.reader.read = AsyncMock(return_value=b"raw data")
        local_service.request = AsyncMock(return_value=mock_response)
        result = await local_service.shell_raw("echo raw data")
        assert result == b"raw data"

    @pytest.mark.asyncio
    async def test_adbd_tcpip(self, local_service, mock_response):
        """测试开启 TCPIP 模式"""
        mock_response.reader.read = AsyncMock(
            return_value=b"restarting in TCP mode port: 5555"
        )
        local_service.request = AsyncMock(return_value=mock_response)
        result = await local_service.adbd_tcpip(5555)
        assert "restarting in TCP mode port" in result

    @pytest.mark.asyncio
    async def test_adbd_root(self, local_service, mock_response):
        """测试切换到 root 模式"""
        mock_response.reader.read = AsyncMock(return_value=b"restarting adbd as root")
        local_service.request = AsyncMock(return_value=mock_response)
        await local_service.adbd_root()

    @pytest.mark.asyncio
    async def test_adbd_unroot(self, local_service, mock_response):
        """测试切换到非 root 模式"""
        mock_response.reader.read = AsyncMock(
            return_value=b"restarting adbd as non root"
        )
        local_service.request = AsyncMock(return_value=mock_response)
        await local_service.adbd_unroot()

    @pytest.mark.asyncio
    async def test_remount(self, local_service, mock_response):
        """测试重新挂载"""
        mock_response.reader.read = AsyncMock(return_value=b"remount succeeded")
        local_service.request = AsyncMock(return_value=mock_response)
        result = await local_service.remount()
        assert "remount succeeded" in result

    @pytest.mark.asyncio
    async def test_reverse_list(self, local_service, mock_response):
        """测试列出反向代理规则"""
        reverse_output = """tcp tcp:8080 tcp:8080
"""
        mock_response.text = AsyncMock(return_value=reverse_output)
        local_service.request = AsyncMock(return_value=mock_response)
        rules = await local_service.reverse_list()
        assert len(rules) == 1
