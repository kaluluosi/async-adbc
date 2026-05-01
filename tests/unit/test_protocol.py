"""协议测试模块"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from async_adbc.protocol.connection import (
    encode_length,
    decode_length,
    pack,
    Connection,
)
from async_adbc.protocol.response import Response


class TestEncodeDecode:
    """测试编解码函数"""

    def test_encode_length(self):
        """测试长度编码"""
        assert encode_length(4) == b"0004"
        assert encode_length(16) == b"0010"
        assert encode_length(255) == b"00ff"

    def test_decode_length(self):
        """测试长度解码"""
        assert decode_length(b"0004") == 4
        assert decode_length(b"0010") == 16
        assert decode_length(b"00ff") == 255

    def test_pack(self):
        """测试消息打包"""
        assert pack("test") == b"0004test"
        assert pack("hello world") == b"000bhello world"


class TestConnection:
    """测试 Connection 类"""

    @pytest.fixture
    def mock_reader(self):
        """Mock StreamReader"""
        reader = MagicMock()
        reader.read = AsyncMock(return_value=b"OKAY")
        reader.readexactly = AsyncMock(return_value=b"OKAY")
        return reader

    @pytest.fixture
    def mock_writer(self):
        """Mock StreamWriter"""
        writer = MagicMock()
        writer.write = MagicMock()
        writer.drain = AsyncMock()
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock()
        return writer

    @pytest.fixture
    def conn(self, mock_reader, mock_writer):
        """创建 Connection 对象"""
        return Connection(mock_reader, mock_writer)

    @pytest.mark.asyncio
    async def test_request(self, conn, mock_reader, mock_writer):
        """测试 request 方法"""
        mock_reader.read = AsyncMock(side_effect=[b"OKAY", b"0005hello"])
        response = await conn.request("host:version")
        mock_writer.write.assert_called_once_with(b"000chost:version")
        assert isinstance(response, Response)

    @pytest.mark.asyncio
    async def test_request_without_check(self, conn, mock_writer):
        """测试 request_without_check 方法"""
        response = await conn.request_without_check("host:version")
        mock_writer.write.assert_called_once_with(b"000chost:version")
        assert isinstance(response, Response)

    @pytest.mark.asyncio
    async def test_check_status_okay(self, conn, mock_reader):
        """测试检查 OKAY 状态"""
        mock_reader.read = AsyncMock(return_value=b"OKAY")
        result = await conn._check_status()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_status_fail(self, conn, mock_reader):
        """测试检查 FAIL 状态"""
        mock_reader.read = AsyncMock(side_effect=[b"FAIL", b"0008error msg"])
        with pytest.raises(RuntimeError):
            await conn._check_status()

    def test_close(self, conn, mock_writer):
        """测试关闭连接"""
        conn.close()
        mock_writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, conn, mock_writer):
        """测试异步上下文管理器"""
        async with conn:
            pass
        mock_writer.close.assert_called_once()


class TestResponse:
    """测试 Response 类"""

    @pytest.fixture
    def mock_reader(self):
        """Mock StreamReader"""
        reader = MagicMock()
        return reader

    @pytest.fixture
    def mock_writer(self):
        """Mock StreamWriter"""
        writer = MagicMock()
        return writer

    @pytest.fixture
    def response(self, mock_reader, mock_writer):
        """创建 Response 对象"""
        return Response(mock_reader, mock_writer)

    @pytest.mark.asyncio
    async def test_read(self, response, mock_reader):
        """测试读取响应"""
        mock_reader.read = AsyncMock(return_value=b"test data")
        data = await response.read()
        assert data == b"test data"

    @pytest.mark.asyncio
    async def test_text(self, response, mock_reader):
        """测试读取响应文本"""
        mock_reader.read = AsyncMock(return_value=b"test text")
        text = await response.text()
        assert text == "test text"
