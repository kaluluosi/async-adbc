"""模型测试模块"""
import pytest
from async_adbc.models import (
    DeviceStatusNotification,
    ForwardRule,
    ReverseRule,
    CPUInfo,
    CPUUsage,
    CPUFreq,
    CPUStat,
    ProcessCPUStat,
    MemInfo,
    MemStat,
    TempStat,
    FpsStat,
)


@pytest.mark.unit
class TestDeviceStatusNotification:
    """测试 DeviceStatusNotification 模型"""

    def test_create(self):
        """测试创建设备状态通知"""
        notif = DeviceStatusNotification(serialno="emulator-5554", status="device")
        assert notif.serialno == "emulator-5554"
        assert notif.status == "device"


@pytest.mark.unit
class TestForwardRule:
    """测试 ForwardRule 模型"""

    def test_create(self):
        """测试创建转发规则"""
        rule = ForwardRule(serialno="emulator-5554", local="tcp:8080", remote="tcp:8080")
        assert rule.serialno == "emulator-5554"
        assert rule.local == "tcp:8080"
        assert rule.remote == "tcp:8080"


@pytest.mark.unit
class TestReverseRule:
    """测试 ReverseRule 模型"""

    def test_create(self):
        """测试创建反向代理规则"""
        rule = ReverseRule(type="tcp", local="tcp:8080", remote="tcp:8080")
        assert rule.type == "tcp"
        assert rule.local == "tcp:8080"
        assert rule.remote == "tcp:8080"


@pytest.mark.unit
class TestCPUFreq:
    """测试 CPUFreq 模型"""

    def test_create(self):
        """测试创建 CPU 频率对象"""
        freq = CPUFreq(min=1000000, cur=2000000, max=3000000)
        assert freq.min == 1000000
        assert freq.cur == 2000000
        assert freq.max == 3000000

    def test_default(self):
        """测试创建默认值 CPU 频率对象"""
        freq = CPUFreq()
        assert freq.min == 0
        assert freq.cur == 0
        assert freq.max == 0


@pytest.mark.unit
class TestCPUStat:
    """测试 CPUStat 模型"""

    def test_create(self):
        """测试创建 CPU 统计对象"""
        stat = CPUStat(
            user=100,
            nice=200,
            system=300,
            idle=400,
            iowait=50,
            irq=60,
            softirq=70,
            stealstolen=80,
            guest=90,
            guest_nice=100,
        )
        assert stat.user == 100
        assert stat.total == 100 + 200 + 300 + 400 + 50 + 60 + 70 + 80 + 90 + 100

    def test_subtract(self):
        """测试 CPU 统计对象减法"""
        stat1 = CPUStat(user=200, idle=400)
        stat2 = CPUStat(user=100, idle=200)
        diff = stat1 - stat2
        assert diff.user == 100
        assert diff.idle == 200

    def test_usage(self):
        """测试 CPU 使用率计算"""
        stat = CPUStat(user=50, system=50, idle=100)
        assert stat.usage == 50.0


@pytest.mark.unit
class TestCPUUsage:
    """测试 CPUUsage 模型"""

    def test_create(self):
        """测试创建 CPU 使用率对象"""
        usage = CPUUsage(usage=50.5, normalized=25.25)
        assert usage.usage == 50.5
        assert usage.normalized == 25.25

    def test_default(self):
        """测试创建默认值 CPU 使用率对象"""
        usage = CPUUsage()
        assert usage.usage == 0.0
        assert usage.normalized == 0.0


@pytest.mark.unit
class TestCPUInfo:
    """测试 CPUInfo 模型"""

    def test_create(self):
        """测试创建 CPU 信息对象"""
        info = CPUInfo(
            platform="msm8998",
            name="Qualcomm Snapdragon 835",
            abi="arm64-v8a",
            core=8,
            freq=(1000000, 3000000),
        )
        assert info.platform == "msm8998"
        assert info.core == 8


@pytest.mark.unit
class TestProcessCPUStat:
    """测试 ProcessCPUStat 模型"""

    def test_create(self):
        """测试创建进程 CPU 统计对象"""
        stat = ProcessCPUStat(
            name="test",
            utime=1000,
            stime=2000,
            cutime=300,
            cstime=400,
        )
        assert stat.name == "test"
        assert stat.total == 1000 + 2000 + 300 + 400

    def test_subtract(self):
        """测试进程 CPU 统计对象减法"""
        stat1 = ProcessCPUStat(utime=2000, stime=4000)
        stat2 = ProcessCPUStat(utime=1000, stime=2000)
        diff = stat1 - stat2
        assert diff.utime == 1000
        assert diff.stime == 2000


@pytest.mark.unit
class TestMemInfo:
    """测试 MemInfo 模型"""

    def test_create(self):
        """测试创建内存信息对象"""
        info = MemInfo(mem_total=1000000, swap_total=500000)
        assert info.mem_total == 1000000
        assert info.swap_total == 500000

    def test_default(self):
        """测试创建默认值内存信息对象"""
        info = MemInfo()
        assert info.mem_total == 0
        assert info.swap_total == 0


@pytest.mark.unit
class TestMemStat:
    """测试 MemStat 模型"""

    def test_create(self):
        """测试创建内存统计对象"""
        stat = MemStat(
            pss=10000,
            private_dirty=8000,
            private_clean=2000,
            swapped_dirty=500,
            heap_size=20000,
            heap_alloc=15000,
            heap_free=5000,
        )
        assert stat.pss == 10000

    def test_default(self):
        """测试创建默认值内存统计对象"""
        stat = MemStat()
        assert stat.pss == 0


@pytest.mark.unit
class TestTempStat:
    """测试 TempStat 模型"""

    def test_create(self):
        """测试创建温度统计对象"""
        stat = TempStat(cpu=35.5, gpu=36.0, skin=34.5, battery=35.0)
        assert stat.cpu == 35.5
        assert stat.gpu == 36.0

    def test_default(self):
        """测试创建默认值温度统计对象"""
        stat = TempStat()
        assert stat.cpu == 0.0


@pytest.mark.unit
class TestFpsStat:
    """测试 FpsStat 模型"""

    def test_create(self):
        """测试创建 FPS 统计对象"""
        stat = FpsStat(fps=60.0, jank=2, big_jank=0)
        assert stat.fps == 60.0
        assert stat.jank == 2

    def test_default(self):
        """测试创建默认值 FPS 统计对象"""
        stat = FpsStat()
        assert stat.fps == 0.0
