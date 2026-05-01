import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from async_adbc.client import ADBClient
from async_adbc.device import Device
from async_adbc.protocol.connection import Connection
from async_adbc.models import DeviceStatusNotification, ForwardRule, ReverseRule


@pytest.fixture
def mock_reader():
    reader = MagicMock()
    reader.read = AsyncMock(return_value=b"OKAY")
    reader.readexactly = AsyncMock(return_value=b"OKAY")
    return reader


@pytest.fixture
def mock_writer():
    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    return writer


@pytest.fixture
def mock_connection(mock_reader, mock_writer):
    conn = MagicMock(spec=Connection)
    conn.reader = mock_reader
    conn.writer = mock_writer
    conn.request = AsyncMock()
    conn.request_without_check = AsyncMock()
    conn.transport_mode = AsyncMock()
    conn.message = AsyncMock()
    conn._check_status = AsyncMock()
    conn.close = MagicMock()
    return conn


@pytest.fixture
def mock_adbclient(mock_connection):
    client = MagicMock(spec=ADBClient)
    client.host = "127.0.0.1"
    client.port = 5037
    client.create_connection = AsyncMock(return_value=mock_connection)
    client.request = AsyncMock()
    client.devices = AsyncMock(return_value=[])
    client.device = AsyncMock()
    client.version = AsyncMock(return_value=41)
    client.kill = AsyncMock()
    client.remote_connect = AsyncMock(return_value=True)
    client.remote_disconnect = AsyncMock(return_value="")
    client.forward_list = AsyncMock(return_value=[])
    client.forward = AsyncMock()
    client.forward_remove = AsyncMock()
    client.forward_remove_all = AsyncMock()
    client.devices_track = AsyncMock()
    return client


@pytest.fixture
def mock_device(mock_adbclient, mock_connection):
    device = MagicMock(spec=Device)
    device.adbc = mock_adbclient
    device.serialno = "emulator-5554"
    device.create_connection = AsyncMock(return_value=mock_connection)
    device.shell = AsyncMock(return_value="")
    device.shell_raw = AsyncMock(return_value=b"")
    device.shell_reader = AsyncMock()
    device.adbd_tcpip = AsyncMock(return_value="")
    device.adbd_root = AsyncMock()
    device.adbd_unroot = AsyncMock()
    device.reboot = AsyncMock()
    device.remount = AsyncMock()
    device.push = AsyncMock()
    device.pull = AsyncMock()
    device.reverse_list = AsyncMock(return_value=[])
    device.reverse = AsyncMock()
    device.reverse_remove = AsyncMock()
    device.reverse_remove_all = AsyncMock()
    device.get_pid_by_pkgname = AsyncMock(return_value=1234)
    device.file_exists = AsyncMock(return_value=True)
    device.close = MagicMock()
    return device


@pytest.fixture
def mock_shell_output(mock_device):
    def _mock_shell_output(cmd: str, output: str):
        mock_device.shell.side_effect = lambda c, *args: output if c in cmd or cmd in c else ""
    return _mock_shell_output


@pytest.fixture
def mock_shell_raw_output(mock_device):
    def _mock_shell_raw_output(cmd: str, output: bytes):
        mock_device.shell_raw.side_effect = lambda c, *args: output if c in cmd or cmd in c else b""
    return _mock_shell_raw_output


@pytest.fixture
def sample_cpuinfo_output():
    return """
processor       : 0
BogoMIPS        : 38.40
Features        : fp asimd evtstrm aes pmull sha1 sha2 crc32
CPU implementer : 0x41
CPU architecture: 8
CPU variant     : 0x0
CPU part        : 0xd03
CPU revision    : 4
Hardware        : Qualcomm Technologies, Inc MSM8998
"""


@pytest.fixture
def sample_proc_stat_output():
    return """cpu  4321 123 4567 89012 234 567 890 123 456 789
cpu0 1234  45 1234 23456  67 123 456  78  89  90
cpu1  987  32  987 21098  56  98 321  45  56  67
cpu2 1111  28 1111 22222  55  89 222  44  55  66
cpu3  989  18 1235 22236  56 157  91  56  56  66
intr 123456 789 ...
ctxt 987654321
btime 1234567890
processes 12345
procs_running 1
procs_blocked 0
"""


@pytest.fixture
def sample_meminfo_output():
    return """MemTotal:        5872084 kB
MemFree:         2156789 kB
MemAvailable:    3456789 kB
Buffers:           12345 kB
Cached:          1234567 kB
SwapCached:        12345 kB
SwapTotal:       1234567 kB
SwapFree:        1234567 kB
"""


@pytest.fixture
def sample_dumpsys_meminfo_output():
    return """Applications Memory Usage (in Kilobytes):
Uptime: 1234567 Realtime: 1234567

** MEMINFO in pid 1234 [com.test.app] **
                    Pss  Private  Private  SwapPss     Heap     Heap     Heap
                  Total    Dirty    Clean    Dirty     Size    Alloc     Free
                 ------   ------   ------   ------   ------   ------   ------
  Native Heap     1234     1111        0      123     2222     1111     1111
  Dalvik Heap     4567     3456        0       45     5678     3456     2222
 Dalvik Other      123      111        0        0
        Stack       45       45        0        0
    Other dev       12        0       12        0
     .so mmap      789       67      567        0
    .apk mmap      123        0       89        0
    .ttf mmap       45        0       45        0
    .dex mmap      567        1      456        0
    .oat mmap       89        0       89        0
    .art mmap      456      400        0        0
   Other mmap       56        8       32        0
      Unknown      111      100        0        0
        TOTAL     8234     5298     1190      168     7900     4567     3333

 App Summary
                       Pss(KB)
                        ------
           Java Heap:     3856
         Native Heap:     1111
                Code:     1078
               Stack:       45
            Graphics:        0
       Private Other:      123
              System:      201
               TOTAL:     8234      TOTAL SWAP PSS:      168

 Objects
               Views:       45         ViewRootImpl:        1
         AppContexts:        3           Activities:        1
              Assets:        4        AssetManagers:        2
       Local Binders:       12        Proxy Binders:       23
       Parcel memory:        2         Parcel count:        8
    Death Recipients:        1      OpenSSL Sockets:        0
            WebViews:        0

 SQL
         MEMORY_USED:       123
  PAGECACHE_OVERFLOW:        45          MALLOC_SIZE:       567
"""
