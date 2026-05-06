"""
Scrcpy plugin implementation using pyscrcpy library.

This plugin provides Android device screen mirroring and control functionality
using the mature pyscrcpy library instead of custom protocol implementation.
"""
import asyncio
import threading
import queue
import time
from typing import Optional, Callable, Any, Dict, Generator, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor

from async_adbc.plugin import Plugin, register_plugin

if TYPE_CHECKING:
    from async_adbc.device import Device

# Try to import pyscrcpy, but don't fail if not available
try:
    from pyscrcpy import Client
    HAS_PYSCRCPY = True
except ImportError:
    HAS_PYSCRCPY = False
    Client = None


@register_plugin("scrcpy", "scrcpy")
class ScrcpyPlugin(Plugin):
    """
    Scrcpy plugin for Android device screen mirroring and control.
    
    This implementation uses the pyscrcpy library which provides a mature
    and stable implementation of the scrcpy protocol.
    """
    
    def __init__(self, device: "Device"):
        super().__init__(device)
        
        # pyscrcpy client and related state
        self._client = None
        self._is_running = False
        self._executor = None
        self._frame_queue = queue.Queue(maxsize=10)
        self._frame_callback = None
        self._device_info = {}
        
        # Thread safety
        self._lock = threading.Lock()
    
    async def init(self):
        """
        Initialize scrcpy. 
        
        Note: pyscrcpy handles server deployment automatically,
        so this method doesn't need to push any files.
        """
        if not HAS_PYSCRCPY:
            raise RuntimeError(
                "pyscrcpy is not installed. "
                "Please install it with: pip install pyscrcpy "
                "or install async-adbc with scrcpy extras: "
                "pip install async-adbc[scrcpy]"
            )
        
        # Check if scrcpy-server.jar exists on device (pyscrcpy will handle this)
        # We don't need to push it manually
        
        return
    
    async def check_device_support(self) -> dict:
        """
        Check if device supports scrcpy.
        
        Returns:
            dict: Dictionary containing support information and warnings
        """
        result = {
            'supported': True,
            'warnings': [],
            'device_info': {}
        }
        
        try:
            # Get device information
            api_level = await self._device.shell("getprop ro.build.version.sdk")
            android_version = await self._device.shell("getprop ro.build.version.release")
            cpu_abi = await self._device.shell("getprop ro.product.cpu.abi")
            
            result['device_info'] = {
                'api_level': api_level.strip(),
                'android_version': android_version.strip(),
                'cpu_abi': cpu_abi.strip()
            }
            
            # Check API level
            try:
                api = int(api_level.strip())
                if api < 21:
                    result['supported'] = False
                    result['warnings'].append(f"API level {api} is too low, requires API 21+ (Android 5.0+)")
            except ValueError:
                pass
            
            # Check if emulator
            if 'emulator' in cpu_abi.lower() or '127.0.0.1:' in self._device.serialno:
                result['warnings'].append("Detected emulator, scrcpy server might be unstable")
            
            # scrcpy-server.jar is pure Java, theoretically not limited by CPU architecture
            # But x86 emulators might have some instability
            if 'x86' in cpu_abi.lower() and 'emulator' in self._device.serialno.lower():
                result['warnings'].append("Detected x86 architecture emulator, scrcpy might be unstable on emulator")
            
        except Exception as e:
            result['warnings'].append(f"Error checking device support: {e}")
        
        return result
    
    async def start(
        self,
        max_size: int = 720,
        bit_rate: int = 2000000,
        check_support: bool = True,
        queue_size: int = 10,
        max_fps: int = 15
    ):
        """
        Start scrcpy screen mirroring.
        
        Args:
            max_size: Maximum dimension of video stream (width or height)
            bit_rate: Video bit rate in bits per second
            check_support: Whether to check device support before starting
            queue_size: Maximum frame queue size
            max_fps: Maximum frames per second (0 for no limit)
            
        Raises:
            RuntimeError: If pyscrcpy is not installed or device not supported
        """
        if not HAS_PYSCRCPY:
            raise RuntimeError(
                "pyscrcpy is not installed. "
                "Please install it with: pip install pyscrcpy"
            )
        
        if self._is_running:
            return
        
        # Check device support if requested
        if check_support:
            support_info = await self.check_device_support()
            if not support_info['supported']:
                raise RuntimeError(f"Device not supported: {support_info['warnings']}")
        
        # Create executor for running pyscrcpy in background thread
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._frame_queue = queue.Queue(maxsize=queue_size)
        
        # Start pyscrcpy client in background thread
        loop = asyncio.get_event_loop()
        
        def start_client():
            """Start pyscrcpy client in background thread"""
            with self._lock:
                # Create pyscrcpy client
                self._client = Client(
                    device=self._device.serialno,
                    max_size=max_size,
                    bitrate=bit_rate,
                    max_fps=max_fps,
                    block_frame=True,
                    stay_awake=True,
                    skip_same_frame=False
                )
                
                # Set up frame callback
                def on_frame(client, frame):
                    """Callback for each frame received"""
                    try:
                        # Put frame in queue (non-blocking)
                        self._frame_queue.put_nowait(frame)
                    except queue.Full:
                        # Drop oldest frame if queue is full
                        try:
                            self._frame_queue.get_nowait()
                            self._frame_queue.put_nowait(frame)
                        except queue.Empty:
                            pass
                    
                    # Call user callback if set
                    if self._frame_callback:
                        try:
                            self._frame_callback(frame)
                        except Exception:
                            pass
                
                self._client.on_frame(on_frame)
                
                # Start client (threaded mode)
                self._client.start(threaded=True)
                
                # Store device info
                if self._client.device_name:
                    self._device_info['device_name'] = self._client.device_name
                if self._client.resolution:
                    self._device_info['width'] = self._client.resolution[0]
                    self._device_info['height'] = self._client.resolution[1]
                
                self._is_running = True
        
        # Run in executor
        await loop.run_in_executor(self._executor, start_client)
        
        # Wait a bit for client to initialize
        await asyncio.sleep(1.0)
    
    async def stop(self):
        """Stop scrcpy screen mirroring."""
        if not self._is_running:
            return
        
        def stop_client():
            """Stop pyscrcpy client in background thread"""
            with self._lock:
                if self._client:
                    # Stop the client
                    self._client.alive = False
                    self._client = None
                
                self._is_running = False
                self._device_info = {}
                
                # Clear frame queue
                while not self._frame_queue.empty():
                    try:
                        self._frame_queue.get_nowait()
                    except queue.Empty:
                        break
        
        # Run in executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, stop_client)
        
        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
    
    def set_frame_callback(self, callback: Callable[[Any], None]):
        """
        Set callback for frame updates.
        
        Args:
            callback: Function that will be called with each new frame
        """
        self._frame_callback = callback
    
    async def get_frame(self, timeout: float = 1.0) -> Optional[Any]:
        """
        Get the latest frame from the queue.
        
        Args:
            timeout: Maximum time to wait for a frame (seconds)
            
        Returns:
            Latest frame (numpy array) or None if no frame available
        """
        if not self._is_running or self._frame_queue.empty():
            return None
        
        try:
            # Try to get frame without blocking
            return self._frame_queue.get_nowait()
        except queue.Empty:
            # Wait for frame with timeout
            try:
                return await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: self._frame_queue.get(timeout=timeout)
                    ),
                    timeout=timeout
                )
            except (asyncio.TimeoutError, queue.Empty):
                return None
    
    async def wait_for_frame(self, timeout: float = 5.0) -> Optional[Any]:
        """
        Wait for a frame to become available.
        
        Args:
            timeout: Maximum time to wait (seconds)
            
        Returns:
            Frame (numpy array) or None if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            frame = await self.get_frame(timeout=0.1)
            if frame is not None:
                return frame
            await asyncio.sleep(0.01)
        return None
    
    async def stream_frames(self) -> Generator[Any, None, None]:
        """
        Async generator that yields frames as they arrive.
        
        Yields:
            Frame (numpy array)
        """
        while self._is_running:
            frame = await self.get_frame(timeout=0.1)
            if frame is not None:
                yield frame
            else:
                await asyncio.sleep(0.01)
    
    async def record(self, output_path: str, duration: Optional[float] = None):
        """
        Record video to file.
        
        Args:
            output_path: Output file path
            duration: Recording duration in seconds (None for indefinite)
            
        Note: This is a basic implementation that saves frames as images.
        For proper video recording, consider using OpenCV VideoWriter.
        """
        if not self._is_running:
            raise RuntimeError("Scrcpy not running, call start() first")
        
        try:
            import cv2
        except ImportError:
            raise RuntimeError("OpenCV is required for recording. Install with: pip install opencv-python")
        
        # Get first frame to determine video properties
        first_frame = await self.wait_for_frame(timeout=5.0)
        if first_frame is None:
            raise RuntimeError("No frames received, cannot start recording")
        
        height, width = first_frame.shape[:2]
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 15  # Default FPS
        
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        try:
            start_time = time.time()
            frame_count = 0
            
            async for frame in self.stream_frames():
                out.write(frame)
                frame_count += 1
                
                if duration and (time.time() - start_time >= duration):
                    break
                
                # Limit recording frame rate
                await asyncio.sleep(1.0 / fps)
        finally:
            out.release()
    
    async def screencap(self, timeout: float = 1.0):
        """
        Capture a screenshot.
        
        Args:
            timeout: Maximum time to wait for a frame (seconds)
            
        Returns:
            Frame (numpy array) or None if timeout
        """
        return await self.wait_for_frame(timeout=timeout)
    
    # Control methods (delegated to pyscrcpy)
    
    async def tap(self, x: int, y: int):
        """
        Tap at coordinates (x, y).
        
        This is a convenience method that performs touch down and up.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        await self.touch(x, y, action=0)  # DOWN
        await asyncio.sleep(0.05)  # Short delay
        await self.touch(x, y, action=1)  # UP
    
    async def touch(self, x: int, y: int, action: int = 0, pointer_id: int = -1):
        """
        Simulate touch event.
        
        Args:
            x: X coordinate
            y: Y coordinate
            action: 0=DOWN, 1=UP, 2=MOVE (default: 0=DOWN)
            pointer_id: Pointer ID (default: -1 for first pointer)
        """
        if not self._is_running or not self._client:
            raise RuntimeError("Scrcpy not running, call start() first")
        
        def do_touch():
            with self._lock:
                if self._client and self._client.control:
                    self._client.control.touch(x, y, action, pointer_id)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, do_touch)
    
    async def keycode(self, keycode: int):
        """
        Send keycode event (press and release).
        
        Args:
            keycode: Android keycode
        """
        await self.key(keycode, action=0)  # DOWN
        await asyncio.sleep(0.05)  # Short delay
        await self.key(keycode, action=1)  # UP
    
    async def key(self, keycode: int, action: int = 0, repeat: int = 0):
        """
        Simulate key event.
        
        Args:
            keycode: Android keycode
            action: 0=DOWN, 1=UP (default: 0=DOWN)
            repeat: Repeat count
        """
        if not self._is_running or not self._client:
            raise RuntimeError("Scrcpy not running, call start() first")
        
        def do_key():
            with self._lock:
                if self._client and self._client.control:
                    self._client.control.key(keycode, action, repeat)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, do_key)
    
    async def text(self, text: str):
        """
        Input text.
        
        Args:
            text: Text to input
        """
        if not self._is_running or not self._client:
            raise RuntimeError("Scrcpy not running, call start() first")
        
        def do_text():
            with self._lock:
                if self._client and self._client.control:
                    self._client.control.text(text)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, do_text)
    
    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                    duration_ms: int = 100, steps: int = 10):
        """
        Simulate swipe gesture.
        
        Args:
            start_x: Start X coordinate
            start_y: Start Y coordinate
            end_x: End X coordinate
            end_y: End Y coordinate
            duration_ms: Duration in milliseconds
            steps: Number of steps in the swipe
        """
        if not self._is_running or not self._client:
            raise RuntimeError("Scrcpy not running, call start() first")
        
        # Implement swipe as a series of touch moves
        await self.touch(start_x, start_y, action=0)  # DOWN
        
        for i in range(1, steps + 1):
            ratio = i / steps
            x = int(start_x + (end_x - start_x) * ratio)
            y = int(start_y + (end_y - start_y) * ratio)
            await self.touch(x, y, action=2)  # MOVE
            await asyncio.sleep(duration_ms / 1000.0 / steps)
        
        await self.touch(end_x, end_y, action=1)  # UP
    
    # Properties
    
    @property
    def device_name(self) -> Optional[str]:
        """Get device name."""
        return self._device_info.get('device_name')
    
    @property
    def resolution(self) -> Optional[tuple]:
        """Get screen resolution (width, height)."""
        if 'width' in self._device_info and 'height' in self._device_info:
            return (self._device_info['width'], self._device_info['height'])
        return None
    
    @property
    def is_running(self) -> bool:
        """Check if scrcpy is running."""
        return self._is_running