"""Scrcpy 插件 - 基于 scrcpy-server v3.3.4"""

import os
import socket
import struct
import asyncio
import logging
from typing import Optional, Tuple, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from io import BytesIO

from async_adbc.plugin import Plugin, register_plugin

# 尝试导入 PIL 和 av
try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import av
except ImportError:
    av = None


logger = logging.getLogger(__name__)


class ScrcpyError(Exception):
    """Scrcpy 相关错误"""
    pass


class DeviceInfo:
    """设备信息"""
    def __init__(self, dummy: bytes, name: str, width: int, height: int):
        self.dummy = dummy
        self.name = name
        self.width = width
        self.height = height


class ScrcpySession:
    """Scrcpy 会话 - 管理与设备的连接"""

    def __init__(
        self,
        device,
        server_path: str,
        max_size: int = 0,
        max_fps: int = 0,
        bit_rate: int = 8000000,
        stay_awake: bool = True,
    ):
        self._device = device
        self._server_path = server_path
        self._max_size = max_size
        self._max_fps = max_fps
        self._bit_rate = bit_rate
        self._stay_awake = stay_awake

        self._server_reader = None
        self._client_sock = None
        self._server_sock = None
        self._port = None
        self._device_info: Optional[DeviceInfo] = None

        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
        self._frame_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=10)

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        return self._device_info

    async def start(self):
        """启动 scrcpy 会话"""
        if self._running:
            return

        # 1. 清理旧的 reverse
        await self._device.reverse_remove_all()

        # 2. 推送 server
        remote_path = "/data/local/tmp/scrcpy-server"
        await self._device.push(self._server_path, remote_path)

        # 3. 找一个可用端口并监听
        self._port = await self._find_available_port()
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.settimeout(10.0)
        self._server_sock.bind(("127.0.0.1", self._port))
        self._server_sock.listen(1)
        logger.debug(f"Listening on port {self._port}")

        # 4. 设置 reverse (关键: 参数顺序!)
        # device.reverse(remote_host, local_abstract)
        await self._device.reverse(f"tcp:{self._port}", "localabstract:scrcpy")

        # 5. 启动 server (用 shell_reader，不等待!)
        cmd = self._build_server_cmd(remote_path)
        self._server_reader = await self._device.shell_reader(cmd)
        logger.debug("Server started")

        # 6. 接受连接
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                self._client_sock, addr = await loop.run_in_executor(
                    executor, self._server_sock.accept
                )
                logger.debug(f"Accepted connection from {addr}")
            except socket.timeout:
                raise ScrcpyError("Timeout waiting for device connection")

        # 7. 握手
        await self._handshake()

        # 8. 用 WMPlugin 获取真实分辨率（修复握手读取错误问题）
        try:
            if self._device_info:
                res = await self._device.wm.size()
                phys_size = res.physical_size
                if phys_size and "x" in phys_size:
                    w, h = phys_size.split("x")
                    self._device_info.width = int(w)
                    self._device_info.height = int(h)
        except Exception as e:
            logger.debug(f"无法获取真实分辨率: {e}")

        self._running = True

    async def _find_available_port(self) -> int:
        """找一个可用端口"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def _build_server_cmd(self, remote_path: str) -> str:
        """构建启动命令"""
        args = []
        if self._max_size > 0:
            args.append(f"max_size={self._max_size}")
        if self._max_fps > 0:
            args.append(f"max_fps={self._max_fps}")
        args.append(f"bit_rate={self._bit_rate}")
        if self._stay_awake:
            args.append("stay_awake=true")
        # 每10帧一个关键帧，让后续的 screencap() 更容易解码
        args.append("keyframe_interval=10")

        return f"CLASSPATH={remote_path} app_process / com.genymobile.scrcpy.Server 3.3.4 {' '.join(args)}"

    def _recv_exact(self, sock, size):
        """接收 exact number of bytes"""
        data = bytearray()
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ScrcpyError(f"Connection closed, expected {size} bytes, got {len(data)}")
            data.extend(chunk)
        return bytes(data)

    async def _handshake(self):
        """握手协议"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            # 1. dummy byte (1 byte)
            dummy = await loop.run_in_executor(
                executor, lambda: self._recv_exact(self._client_sock, 1)
            )
            if not dummy:
                raise ScrcpyError("Handshake failed: no dummy byte")

            # 2. device name (64 bytes, null-terminated)
            name_bytes = await loop.run_in_executor(
                executor, lambda: self._recv_exact(self._client_sock, 64)
            )
            name = name_bytes.split(b"\x00")[0].decode("utf-8", "replace")

            # 3. width (4 bytes BE)
            width_bytes = await loop.run_in_executor(
                executor, lambda: self._recv_exact(self._client_sock, 4)
            )
            width = int.from_bytes(width_bytes, "big")

            # 4. height (4 bytes BE)
            height_bytes = await loop.run_in_executor(
                executor, lambda: self._recv_exact(self._client_sock, 4)
            )
            height = int.from_bytes(height_bytes, "big")

        self._device_info = DeviceInfo(dummy, name, width, height)
        logger.debug(f"Handshake done: {name} {width}x{height}")

    async def stream_frames(self) -> AsyncGenerator[bytes, None]:
        """异步生成 H.264 帧数据"""
        if not self._running:
            raise ScrcpyError("Session not running")

        loop = asyncio.get_event_loop()
        self._client_sock.settimeout(0.1)

        with ThreadPoolExecutor(max_workers=1) as executor:
            while self._running:
                try:
                    data = await loop.run_in_executor(
                        executor, lambda: self._client_sock.recv(8192)
                    )
                    if data:
                        yield data
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving frame: {e}")
                    break

    async def screencap(self, timeout: float = 3.0) -> bytes:
        """获取 H.264 数据（收集足够的数据用于解码）"""
        buffer = bytearray()
        start_time = asyncio.get_event_loop().time()
        min_duration = 0.5  # 至少收集 0.5 秒的数据（最开始 test_2step.py 成功的参数）
        min_size = 80000  # 至少收集 80K 数据

        async for chunk in self.stream_frames():
            buffer.extend(chunk)

            elapsed = asyncio.get_event_loop().time() - start_time
            # 满足两个条件之一即可
            if elapsed >= min_duration or len(buffer) >= min_size:
                break
            if elapsed >= timeout:
                break

        return bytes(buffer)

    async def record(self, output_path: str, duration: float = 10.0):
        """录制视频到文件"""
        with open(output_path, "wb") as f:
            start_time = asyncio.get_event_loop().time()
            async for chunk in self.stream_frames():
                f.write(chunk)
                if asyncio.get_event_loop().time() - start_time > duration:
                    break

    async def stop(self):
        """停止会话"""
        self._running = False

        # 关闭 socket
        if self._client_sock:
            try:
                self._client_sock.close()
            except Exception:
                pass

        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass

        # 清理 reverse
        try:
            await self._device.reverse_remove_all()
        except Exception:
            pass

        # 删除设备上的 server
        try:
            await self._device.shell("rm /data/local/tmp/scrcpy-server")
        except Exception:
            pass

        logger.debug("Session stopped")


@register_plugin("scrcpy", "scrcpy")
class ScrcpyPlugin(Plugin):
    """Scrcpy 插件 - 提供屏幕录制和截图功能"""

    def __init__(self, device):
        super().__init__(device)
        self._session: Optional[ScrcpySession] = None

        # 找到 vendor 目录下的 scrcpy-server
        self._server_path = self._get_server_path()

    def _get_server_path(self) -> str:
        """获取 scrcpy-server 文件路径"""
        import async_adbc
        pkg_dir = Path(async_adbc.__file__).parent
        server_path = pkg_dir / "vendor" / "scrcpy" / "scrcpy-server-v3.3.4"
        if not server_path.exists():
            # 尝试 jar 后缀
            server_path = pkg_dir / "vendor" / "scrcpy" / "scrcpy-server-v3.3.4.jar"

        if not server_path.exists():
            raise FileNotFoundError(f"scrcpy-server not found at {server_path}")

        return str(server_path)

    async def start(
        self,
        max_size: int = 0,
        max_fps: int = 0,
        bit_rate: int = 8000000,
        stay_awake: bool = True,
    ):
        """启动 scrcpy 会话

        Args:
            max_size: 最大尺寸 (0 表示不限制)
            max_fps: 最大帧率 (0 表示不限制)
            bit_rate: 比特率 (默认 8Mbps)
            stay_awake: 是否保持唤醒
        """
        if self._session:
            await self.stop()

        self._session = ScrcpySession(
            self._device,
            self._server_path,
            max_size=max_size,
            max_fps=max_fps,
            bit_rate=bit_rate,
            stay_awake=stay_awake,
        )
        await self._session.start()

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        """获取设备信息"""
        if self._session:
            return self._session.device_info
        return None

    async def stream_frames(self) -> AsyncGenerator[bytes, None]:
        """异步流式获取 H.264 帧"""
        if not self._session:
            raise ScrcpyError("Session not started, call start() first")

        async for frame in self._session.stream_frames():
            yield frame

    async def screencap(self, save_file: Optional[str] = None, timeout: float = 3.0) -> bytes:
        """获取一帧截图并保存为图片

        Args:
            save_file (str | None, optional): 保存文件，支持 png/jpg/jpeg/h264格式，为空就不保存.
                如果没有扩展名，默认使用 png 格式. Defaults to None.
            timeout (float, optional): 超时时间. Defaults to 5.0.

        Returns:
            bytes: 返回原始 H.264 二进制数据
        """
        if not self._session:
            raise ScrcpyError("Session not started, call start() first")

        result = await self._session.screencap(timeout=timeout)

        if save_file:
            save_path = Path(save_file)
            ext = save_path.suffix.lower()

            # 如果没有扩展名，或者扩展名是图片，都按图片处理（默认png）
            if not ext or ext in [".png", ".jpg", ".jpeg"]:
                if av is None:
                    raise ImportError("需要 av (PyAV) 包来解码 h264，运行: pip install av")
                if Image is None:
                    raise ImportError("需要 Pillow 包来保存图片，运行: pip install pillow")

                # 解码 h264 数据并保存为图片
                image = self._decode_h264_to_image(result)
                if image:
                    # 默认 png
                    fmt = ext[1:] if ext else "png"
                    # 如果没有扩展名，加上 .png
                    final_path = save_path if ext else save_path.with_suffix(".png")
                    image.save(str(final_path), format=fmt)
                else:
                    raise ScrcpyError("无法解码 h264 数据")
            else:
                # 保存原始 h264
                with open(save_file, "wb") as f:
                    f.write(result)

        return result

    def _decode_h264_to_image(self, h264_data: bytes):
        """将 H.264 数据解码为 PIL Image"""
        try:
            # 用 BytesIO，简单稳定
            container = av.open(BytesIO(h264_data))  # type: ignore
            # 找到第一幅完整的画面
            for frame in container.decode(video=0):
                img = frame.to_image()
                container.close()
                return img
        except Exception as e:
            logger.error(f"解码 h264 失败: {e}")
        return None

    async def record(self, output_path: str, duration: float = 10.0):
        """录制视频到文件"""
        if not self._session:
            raise ScrcpyError("Session not started, call start() first")

        await self._session.record(output_path, duration=duration)

    async def stop(self):
        """停止 scrcpy 会话"""
        if self._session:
            await self._session.stop()
            self._session = None

    async def __aenter__(self):
        """async with 支持"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 退出"""
        await self.stop()
