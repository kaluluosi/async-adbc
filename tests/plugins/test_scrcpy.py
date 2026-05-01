"""scrcpy 插件测试模块"""

import pytest
import asyncio
import struct
from unittest.mock import AsyncMock, MagicMock, patch

from async_adbc.plugins.scrcpy import ScrcpyPlugin, StreamReceiver, InputController


@pytest.mark.unit
class TestScrcpyPlugin:
    """测试 ScrcpyPlugin 类"""

    @pytest.fixture
    def scrcpy_plugin(self, mock_device):
        """创建 ScrcpyPlugin 对象"""
        return ScrcpyPlugin(mock_device)

    @pytest.mark.asyncio
    async def test_init_file_exists(self, scrcpy_plugin, mock_device):
        """测试 scrcpy-server.jar 已存在时的初始化"""
        mock_device.file_exists = AsyncMock(return_value=True)
        await scrcpy_plugin.init()
        mock_device.push.assert_not_called()

    @pytest.mark.asyncio
    async def test_init_file_not_exists(self, scrcpy_plugin, mock_device):
        """测试 scrcpy-server.jar 不存在时的初始化"""
        mock_device.file_exists = AsyncMock(return_value=False)
        mock_device.push = AsyncMock()

        with patch("os.path.exists", return_value=True):
            with patch("importlib.resources.path"):
                await scrcpy_plugin.init()

        mock_device.push.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_jar_not_found(self, scrcpy_plugin, mock_device):
        """测试找不到 scrcpy-server.jar 时的处理"""
        mock_device.file_exists = AsyncMock(return_value=False)

        with patch("os.path.exists", return_value=False):
            with patch("importlib.resources.path"):
                with pytest.raises(FileNotFoundError):
                    await scrcpy_plugin.init()


@pytest.mark.unit
class TestInputController:
    """测试 InputController 类"""

    @pytest.fixture
    def mock_writer(self):
        """Mock StreamWriter 对象"""
        writer = MagicMock()
        writer.write = MagicMock()
        writer.drain = AsyncMock()
        return writer

    @pytest.fixture
    def input_controller(self, mock_writer):
        """创建 InputController 对象"""
        return InputController(mock_writer, 1080, 1920)

    def test_pack_message(self, input_controller):
        """测试消息打包"""
        msg = input_controller._pack_message(
            InputController.TYPE_INJECT_KEYCODE, b"\x00\x01\x02\x03"
        )
        assert msg == b"\x00\x00\x01\x02\x03"

    @pytest.mark.asyncio
    async def test_send_keycode_event(self, input_controller, mock_writer):
        """测试发送按键事件"""
        await input_controller._send_keycode_event(
            4, InputController.AKEY_EVENT_ACTION_DOWN
        )

        mock_writer.write.assert_called_once()
        written_data = mock_writer.write.call_args[0][0]
        assert len(written_data) == 14  # 1 + 1 + 4 + 4 + 4

        # 验证消息格式
        unpacked = struct.unpack("!BBIii", written_data)
        assert unpacked[0] == InputController.TYPE_INJECT_KEYCODE
        assert unpacked[1] == InputController.AKEY_EVENT_ACTION_DOWN
        assert unpacked[2] == 4  # keycode

    @pytest.mark.asyncio
    async def test_keycode(self, input_controller, mock_writer):
        """测试 keycode 方法（发送 DOWN 和 UP）"""
        await input_controller.keycode(4)

        assert mock_writer.write.call_count == 2
        mock_writer.drain.assert_awaited()

    @pytest.mark.asyncio
    async def test_text(self, input_controller, mock_writer):
        """测试文本输入"""
        test_text = "hello"
        await input_controller.text(test_text)

        mock_writer.write.assert_called_once()
        written_data = mock_writer.write.call_args[0][0]

        # 验证消息格式
        assert written_data[0] == InputController.TYPE_INJECT_TEXT
        text_len = struct.unpack("!H", written_data[1:3])[0]
        assert text_len == len(test_text)
        assert written_data[3:].decode("utf-8") == test_text

    @pytest.mark.asyncio
    async def test_send_touch_event(self, input_controller, mock_writer):
        """测试发送触摸事件"""
        await input_controller._send_touch_event(
            InputController.AMOTION_EVENT_ACTION_DOWN, 540, 960, 1.0
        )

        mock_writer.write.assert_called_once()
        written_data = mock_writer.write.call_args[0][0]
        assert len(written_data) == 24  # 1 + 1 + 8 + 4 + 4 + 2 + 4

        # 验证消息格式
        # struct.unpack 不支持 8 字节的负数指针 ID，我们单独验证各部分
        assert written_data[0] == InputController.TYPE_INJECT_TOUCH_EVENT
        assert written_data[1] == InputController.AMOTION_EVENT_ACTION_DOWN
        # 验证坐标转换
        expected_x = int(540 * 0x10000 / 1080)
        expected_y = int(960 * 0x10000 / 1920)
        x_bytes = written_data[10:14]
        y_bytes = written_data[14:18]
        assert int.from_bytes(x_bytes, byteorder="big", signed=True) == expected_x
        assert int.from_bytes(y_bytes, byteorder="big", signed=True) == expected_y

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_tap(self, mock_sleep, input_controller, mock_writer):
        """测试 tap 方法"""
        await input_controller.tap(540, 960)

        # 应该发送 DOWN 和 UP 两个事件
        assert mock_writer.write.call_count == 2


@pytest.mark.unit
class TestStreamReceiver:
    """测试 StreamReceiver 类"""

    @pytest.fixture
    def mock_reader(self):
        """Mock StreamReader 对象"""
        reader = MagicMock()
        return reader

    @pytest.fixture
    def stream_receiver(self, mock_reader):
        """创建 StreamReceiver 对象"""
        return StreamReceiver(mock_reader)

    def test_set_frame_callback(self, stream_receiver):
        """测试设置帧回调"""
        callback = MagicMock()
        stream_receiver.set_frame_callback(callback)
        assert stream_receiver._on_frame == callback

    def test_get_latest_frame(self, stream_receiver):
        """测试获取最新帧"""
        test_frame = b"test frame data"
        stream_receiver._latest_frame = test_frame
        assert stream_receiver.get_latest_frame() == test_frame

    @pytest.mark.asyncio
    async def test_receive_loop(self):
        """测试接收循环"""
        # 创建测试数据
        test_frame = b"test h264 frame"
        header = struct.pack("!QI", 123456789, len(test_frame))

        # Mock reader
        mock_reader = MagicMock()

        # 让 readexactly 先返回 header，再返回 frame，然后抛出 CancelledError
        call_count = 0

        async def mock_readexactly(n):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return header
            elif call_count == 2:
                return test_frame
            else:
                raise asyncio.CancelledError()

        mock_reader.readexactly = mock_readexactly

        receiver = StreamReceiver(mock_reader)
        callback = MagicMock()
        receiver.set_frame_callback(callback)

        # 启动接收循环
        receiver._running = True
        task = asyncio.create_task(receiver._receive_loop())

        # 让协程运行一下
        await asyncio.sleep(0.05)

        # 停止并清理
        receiver._running = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # 验证
        assert receiver.get_latest_frame() == test_frame
        callback.assert_called_once_with(test_frame)
