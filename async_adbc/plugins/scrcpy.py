import os
import asyncio
import struct
import time
from typing import Callable, Optional, TYPE_CHECKING
from collections import deque
from importlib import resources
from async_adbc.plugin import Plugin, register_plugin

if TYPE_CHECKING:
    from async_adbc.device import Device


@register_plugin("scrcpy", "scrcpy")
class ScrcpyPlugin(Plugin):
    PUSH_TO = "/data/local/tmp"
    DEFAULT_PORT = 27183

    def __init__(self, device: "Device"):
        super().__init__(device)
        self._server_response = None  # 保存 Response 对象，防止被 GC
        self._server_reader = None
        self._stream_reader = None
        self._stream_writer = None
        self._is_running = False
        self._stream_receiver = None
        self._input_controller = None
        self._local_port = None
        self._device_info = None

    async def init(self):
        """
        初始化 scrcpy，推送 scrcpy-server.jar 到设备
        """
        # 用 __file__ 定位 vendor 目录，更兼容
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        async_adbc_dir = os.path.dirname(plugin_dir)
        vendor_dir = os.path.join(async_adbc_dir, "vendor")
        SCRCPY_LIBS = os.path.join(vendor_dir, "scrcpy")

        exists = await self._device.file_exists("/data/local/tmp/scrcpy-server.jar")
        if exists:
            return

        jarfile_path = os.path.join(SCRCPY_LIBS, "scrcpy-server.jar")

        if not os.path.exists(jarfile_path):
            raise FileNotFoundError(jarfile_path, "没有找到 scrcpy-server.jar")

        await self._device.push(jarfile_path, self.PUSH_TO + "/scrcpy-server.jar", chmod=0o644)

    async def start(self, max_size: int = 0, bit_rate: int = 8000000, port: Optional[int] = None, queue_size: int = 10):
        """
        启动 scrcpy 服务器并建立连接

        Args:
            max_size: 最大分辨率 (0 表示不限制)
            bit_rate: 比特率
            port: 本地端口 (None 则使用默认端口)
            queue_size: 帧队列大小（用于流式输出）
        """
        await self.init()

        self._local_port = port or self.DEFAULT_PORT
        self._queue_size = queue_size

        # 设置端口转发
        await self._device.forward.forward(f"tcp:{self._local_port}", "localabstract:scrcpy")

        # 启动 scrcpy 服务器
        server_cmd = [
            "CLASSPATH=/data/local/tmp/scrcpy-server.jar",
            "app_process",
            "/data/local/tmp",
            "scrcpy.Server",
            "log_level=info",
            f"bit_rate={bit_rate}",
        ]
        if max_size > 0:
            server_cmd.append(f"max_size={max_size}")

        # 直接调用 request（Device 继承自 LocalService），保存 Response 对象，防止被 GC
        self._server_response = await self._device.request("shell", " ".join(server_cmd))
        self._server_reader = self._server_response.reader
        self._is_running = True

        # 建立 socket 连接
        await self._connect()

    async def stop(self):
        """
        停止 scrcpy 服务器
        """
        self._is_running = False

        # 通知 StreamReceiver 的等待者
        if self._stream_receiver:
            async with self._stream_receiver._queue_not_empty:
                self._stream_receiver._queue_not_empty.notify_all()
            await self._stream_receiver.stop()

        # 关闭 socket 连接
        if self._stream_writer:
            self._stream_writer.close()
            await self._stream_writer.wait_closed()

        # 停止服务器进程（关闭 Response）
        if self._server_response:
            try:
                self._server_response.close()
            except Exception:
                pass

        # 移除端口转发
        if self._local_port:
            try:
                await self._device.forward.forward_remove(f"tcp:{self._local_port}")
            except Exception:
                pass

        self._server_response = None
        self._server_reader = None
        self._stream_reader = None
        self._stream_writer = None
        self._stream_receiver = None
        self._input_controller = None
        self._local_port = None
        self._device_info = None

    async def _connect(self):
        """
        建立与 scrcpy 服务器的 socket 连接
        """
        # 等待服务器启动
        await asyncio.sleep(0.5)

        # 连接到本地端口
        self._stream_reader, self._stream_writer = await asyncio.open_connection(
            '127.0.0.1', self._local_port
        )

        # 读取初始设备信息（握手）
        self._device_info = await self._read_device_info()

        # 创建 StreamReceiver 和 InputController
        self._stream_receiver = StreamReceiver(self._stream_reader, queue_size=self._queue_size)
        self._input_controller = InputController(self._stream_writer, self._device_info['width'], self._device_info['height'])

        # 启动接收流
        await self._stream_receiver.start()

    async def _read_device_info(self):
        """
        读取初始设备信息（握手阶段）
        """
        if not self._stream_reader:
            return

        # 读取设备名称长度
        name_len_bytes = await self._stream_reader.readexactly(1)
        name_len = name_len_bytes[0]

        # 读取设备名称
        device_name_bytes = await self._stream_reader.readexactly(name_len)
        device_name = device_name_bytes.decode('utf-8')

        # 读取宽度和高度
        size_bytes = await self._stream_reader.readexactly(4)
        width = int.from_bytes(size_bytes[:2], byteorder='big')
        height = int.from_bytes(size_bytes[2:], byteorder='big')

        return {
            'device_name': device_name,
            'width': width,
            'height': height
        }

    async def get_frame(self) -> Optional[bytes]:
        """
        获取当前视频帧

        Returns:
            bytes: 视频帧数据（H.264 编码）
        """
        if self._stream_receiver:
            return self._stream_receiver.get_latest_frame()
        return None

    async def tap(self, x: int, y: int):
        """
        模拟点击

        Args:
            x: x 坐标
            y: y 坐标
        """
        if self._input_controller:
            await self._input_controller.tap(x, y)

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.3):
        """
        模拟滑动

        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            duration: 持续时间（秒）
        """
        if self._input_controller:
            await self._input_controller.swipe(x1, y1, x2, y2, duration)

    async def keycode(self, keycode: int):
        """
        发送按键事件

        Args:
            keycode: Android 键码
        """
        if self._input_controller:
            await self._input_controller.keycode(keycode)

    async def text(self, text: str):
        """
        输入文本

        Args:
            text: 要输入的文本
        """
        if self._input_controller:
            await self._input_controller.text(text)

    async def screencap(self, timeout: float = 1.0) -> Optional[bytes]:
        """
        截取当前屏幕帧

        Args:
            timeout: 等待帧的超时时间（秒）

        Returns:
            bytes: 视频帧数据（H.264 编码），超时返回 None
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            frame = await self.get_frame()
            if frame:
                return frame
            await asyncio.sleep(0.01)
        return None

    async def stream_frames(self):
        """
        异步生成器，持续生成视频帧

        Yields:
            bytes: 视频帧数据（H.264 编码）
        """
        if not self._stream_receiver:
            return

        async for frame in self._stream_receiver:
            yield frame

    async def record(self, output_path: str, duration: Optional[float] = None):
        """
        录制视频到文件

        Args:
            output_path: 输出文件路径
            duration: 录制时长（秒），None 表示持续录制直到 stop() 被调用
        """
        if not self._is_running:
            raise RuntimeError("Scrcpy not running, call start() first")

        start_time = time.time()

        with open(output_path, 'wb') as f:
            async for frame in self.stream_frames():
                f.write(frame)
                
                if duration and (time.time() - start_time >= duration):
                    break


class StreamReceiver:
    """
    视频流接收类
    """

    def __init__(self, reader: asyncio.StreamReader, queue_size: int = 10):
        self._reader = reader
        self._on_frame = None
        self._task = None
        self._running = False
        self._latest_frame = None
        self._frame_queue = deque(maxlen=queue_size)  # 可配置队列大小
        self._queue_not_empty = asyncio.Condition()  # 条件变量，用于通知队列有新帧

    def set_frame_callback(self, callback: Callable[[bytes], None]):
        """
        设置帧数据回调

        Args:
            callback: 回调函数，接收帧数据作为参数
        """
        self._on_frame = callback

    def get_latest_frame(self) -> Optional[bytes]:
        """
        获取最新的帧数据

        Returns:
            bytes: 最新的视频帧数据
        """
        return self._latest_frame

    async def start(self):
        """
        开始接收流
        """
        self._running = True
        self._task = asyncio.create_task(self._receive_loop())

    async def stop(self):
        """
        停止接收流
        """
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _receive_loop(self):
        """
        接收循环
        """
        try:
            while self._running:
                # Read video packet header: 12 bytes (8 bytes timestamp + 4 bytes length, big-endian)
                header = await self._reader.readexactly(12)
                # Parse timestamp (8 bytes, big-endian) and length (4 bytes, big-endian)
                timestamp, length = struct.unpack('!QI', header)
                # Read the actual frame data
                frame_data = await self._reader.readexactly(length)
                # Store the latest frame
                self._latest_frame = frame_data
                # Add to queue
                self._frame_queue.append(frame_data)
                # Notify waiting consumers
                async with self._queue_not_empty:
                    self._queue_not_empty.notify_all()
                # Call the callback if set
                if self._on_frame:
                    self._on_frame(frame_data)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def __aiter__(self):
        """
        异步迭代器入口
        """
        return self

    async def __anext__(self):
        """
        异步迭代器获取下一帧
        """
        async with self._queue_not_empty:
            # Wait until queue is not empty
            while not self._frame_queue and self._running:
                await self._queue_not_empty.wait()
            
            if not self._running:
                raise StopAsyncIteration
            
            if self._frame_queue:
                return self._frame_queue.popleft()
            else:
                raise StopAsyncIteration


class InputController:
    """
    输入控制类
    """

    # 控制消息类型
    TYPE_INJECT_KEYCODE = 0
    TYPE_INJECT_TEXT = 1
    TYPE_INJECT_TOUCH_EVENT = 2
    TYPE_INJECT_SCROLL_EVENT = 3

    # 触摸事件动作
    AKEY_EVENT_ACTION_DOWN = 0
    AKEY_EVENT_ACTION_UP = 1
    AMOTION_EVENT_ACTION_DOWN = 0
    AMOTION_EVENT_ACTION_UP = 1
    AMOTION_EVENT_ACTION_MOVE = 2

    # Button constants
    AMOTION_EVENT_BUTTON_PRIMARY = 1 << 0

    def __init__(self, writer: asyncio.StreamWriter, screen_width: int, screen_height: int):
        self._writer = writer
        self._screen_width = screen_width
        self._screen_height = screen_height

    async def tap(self, x: int, y: int, pressure: float = 1.0):
        """
        发送点击事件

        Args:
            x, y: 坐标
            pressure: 压力值 (0.0-1.0)
        """
        # Send DOWN event
        await self._send_touch_event(self.AMOTION_EVENT_ACTION_DOWN, x, y, pressure)
        # Send UP event
        await self._send_touch_event(self.AMOTION_EVENT_ACTION_UP, x, y, pressure)

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float):
        """
        发送滑动事件

        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            duration: 持续时间（秒）
        """
        # Send DOWN event
        await self._send_touch_event(self.AMOTION_EVENT_ACTION_DOWN, x1, y1)
        # Calculate steps
        steps = max(int(duration * 60), 2)  # 60 steps per second
        for i in range(1, steps):
            t = i / steps
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            await self._send_touch_event(self.AMOTION_EVENT_ACTION_MOVE, x, y)
            await asyncio.sleep(duration / steps)
        # Send UP event at end position
        await self._send_touch_event(self.AMOTION_EVENT_ACTION_UP, x2, y2)

    async def keycode(self, keycode: int, action: int = None):
        """
        发送按键事件

        Args:
            keycode: Android 键码
            action: 动作 (DOWN/UP) - if None, send both
        """
        if action is None:
            await self._send_keycode_event(keycode, self.AKEY_EVENT_ACTION_DOWN)
            await asyncio.sleep(0.01)
            await self._send_keycode_event(keycode, self.AKEY_EVENT_ACTION_UP)
        else:
            await self._send_keycode_event(keycode, action)

    async def text(self, text: str):
        """
        发送文本输入

        Args:
            text: 要输入的文本
        """
        # Text message: type (1) + length (2 bytes, big-endian) + text (UTF-8)
        data = struct.pack('!BH', self.TYPE_INJECT_TEXT, len(text)) + text.encode('utf-8')
        self._writer.write(data)
        await self._writer.drain()

    async def _send_touch_event(self, action: int, x: int, y: int, pressure: float = 1.0):
        """
        发送触摸事件

        Args:
            action: 动作类型
            x, y: 坐标
            pressure: 压力值
        """
        # Convert coordinates to 16-bit fixed-point (for scrcpy)
        x_scaled = int(x * 0x10000 / self._screen_width)
        y_scaled = int(y * 0x10000 / self._screen_height)
        pressure_scaled = int(pressure * 0xFFFF)
        # Touch event format: type (2) + action (1) + pointer id (8) + x (4) + y (4) + pressure (2) + buttons (4)
        # Use 0xFFFFFFFFFFFFFFFF as pointer id (-1 in two's complement for 64-bit unsigned)
        pointer_id = 0xFFFFFFFFFFFFFFFF
        data = struct.pack(
            '!BBQiiHI',
            self.TYPE_INJECT_TOUCH_EVENT,
            action,
            pointer_id,
            x_scaled,
            y_scaled,
            pressure_scaled,
            self.AMOTION_EVENT_BUTTON_PRIMARY if action in (self.AMOTION_EVENT_ACTION_DOWN, self.AMOTION_EVENT_ACTION_MOVE) else 0
        )
        self._writer.write(data)
        await self._writer.drain()

    async def _send_keycode_event(self, keycode: int, action: int):
        """
        发送按键事件

        Args:
            keycode: Android 键码
            action: 动作 (DOWN/UP)
        """
        # Key event format: type (0) + action (1) + keycode (4) + repeat (4) + meta state (4)
        data = struct.pack('!BBIii', self.TYPE_INJECT_KEYCODE, action, keycode, 0, 0)
        self._writer.write(data)
        await self._writer.drain()

    def _pack_message(self, msg_type: int, data: bytes) -> bytes:
        """
        打包控制消息

        Args:
            msg_type: 消息类型
            data: 消息数据

        Returns:
            bytes: 打包后的消息
        """
        return struct.pack('!B', msg_type) + data
