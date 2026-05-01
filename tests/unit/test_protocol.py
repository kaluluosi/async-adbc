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
    def test_encode_length(self):
        assert encode_length(4) == b"0004"
        assert encode_length(16) == b"0010"
        assert encode_length(255) == b"00ff"

    def test_decode_length(self):
        assert decode_length(b"0004") == 4
        assert decode_length(b"0010") == 16
        assert decode_length(b"00ff") == 255

    def test_pack(self):
        assert pack("test") == b"0004test"
        assert pack("hello world") == b"000bhello world"


class TestConnection:
    @pytest.fixture
    def mock_reader(self):
        reader = MagicMock()
        reader.read = AsyncMock(return_value=b"OKAY")
        reader.readexactly = AsyncMock(return_value=b"OKAY")
        return reader

    @pytest.fixture
    def mock_writer(self):
        writer = MagicMock()
        writer.write = MagicMock()
        writer.drain = AsyncMock()
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock()
        return writer

    @pytest.fixture
    def conn(self, mock_reader, mock_writer):
        return Connection(mock_reader, mock_writer)

    @pytest.mark.asyncio
    async def test_request(self, conn, mock_reader, mock_writer):
        mock_reader.read = AsyncMock(side_effect=[b"OKAY", b"0005hello"])
        response = await conn.request("host:version")
        mock_writer.write.assert_called_once_with(b"000chost:version")
        assert isinstance(response, Response)

    @pytest.mark.asyncio
    async def test_request_without_check(self, conn, mock_writer):
        response = await conn.request_without_check("host:version")
        mock_writer.write.assert_called_once_with(b"000chost:version")
        assert isinstance(response, Response)

    @pytest.mark.asyncio
    async def test_check_status_okay(self, conn, mock_reader):
        mock_reader.read = AsyncMock(return_value=b"OKAY")
        result = await conn._check_status()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_status_fail(self, conn, mock_reader):
        mock_reader.read = AsyncMock(side_effect=[b"FAIL", b"0008error msg"])
        with pytest.raises(RuntimeError):
            await conn._check_status()

    def test_close(self, conn, mock_writer):
        conn.close()
        mock_writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, conn, mock_writer):
        async with conn:
            pass
        mock_writer.close.assert_called_once()


class TestResponse:
    @pytest.fixture
    def mock_reader(self):
        reader = MagicMock()
        return reader

    @pytest.fixture
    def mock_writer(self):
        writer = MagicMock()
        return writer

    @pytest.fixture
    def response(self, mock_reader, mock_writer):
        return Response(mock_reader, mock_writer)

    @pytest.mark.asyncio
    async def test_read(self, response, mock_reader):
        mock_reader.read = AsyncMock(return_value=b"test data")
        data = await response.read()
        assert data == b"test data"

    @pytest.mark.asyncio
    async def test_text(self, response, mock_reader):
        mock_reader.read = AsyncMock(return_value=b"test text")
        text = await response.text()
        assert text == "test text"
