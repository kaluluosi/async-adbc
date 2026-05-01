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


class TestDeviceStatusNotification:
    def test_create(self):
        notif = DeviceStatusNotification(serialno="emulator-5554", status="device")
        assert notif.serialno == "emulator-5554"
        assert notif.status == "device"


class TestForwardRule:
    def test_create(self):
        rule = ForwardRule(serialno="emulator-5554", local="tcp:8080", remote="tcp:8080")
        assert rule.serialno == "emulator-5554"
        assert rule.local == "tcp:8080"
        assert rule.remote == "tcp:8080"


class TestReverseRule:
    def test_create(self):
        rule = ReverseRule(type="tcp", local="tcp:8080", remote="tcp:8080")
        assert rule.type == "tcp"
        assert rule.local == "tcp:8080"
        assert rule.remote == "tcp:8080"


class TestCPUFreq:
    def test_create(self):
        freq = CPUFreq(min=1000000, cur=2000000, max=3000000)
        assert freq.min == 1000000
        assert freq.cur == 2000000
        assert freq.max == 3000000

    def test_default(self):
        freq = CPUFreq()
        assert freq.min == 0
        assert freq.cur == 0
        assert freq.max == 0


class TestCPUStat:
    def test_create(self):
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
        stat1 = CPUStat(user=200, idle=400)
        stat2 = CPUStat(user=100, idle=200)
        diff = stat1 - stat2
        assert diff.user == 100
        assert diff.idle == 200

    def test_usage(self):
        stat = CPUStat(user=50, system=50, idle=100)
        assert stat.usage == 50.0


class TestCPUUsage:
    def test_create(self):
        usage = CPUUsage(usage=50.5, normalized=25.25)
        assert usage.usage == 50.5
        assert usage.normalized == 25.25

    def test_default(self):
        usage = CPUUsage()
        assert usage.usage == 0.0
        assert usage.normalized == 0.0


class TestCPUInfo:
    def test_create(self):
        info = CPUInfo(
            platform="msm8998",
            name="Qualcomm Snapdragon 835",
            abi="arm64-v8a",
            core=8,
            freq=(1000000, 3000000),
        )
        assert info.platform == "msm8998"
        assert info.core == 8


class TestProcessCPUStat:
    def test_create(self):
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
        stat1 = ProcessCPUStat(utime=2000, stime=4000)
        stat2 = ProcessCPUStat(utime=1000, stime=2000)
        diff = stat1 - stat2
        assert diff.utime == 1000
        assert diff.stime == 2000


class TestMemInfo:
    def test_create(self):
        info = MemInfo(mem_total=1000000, swap_total=500000)
        assert info.mem_total == 1000000
        assert info.swap_total == 500000

    def test_default(self):
        info = MemInfo()
        assert info.mem_total == 0
        assert info.swap_total == 0


class TestMemStat:
    def test_create(self):
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
        stat = MemStat()
        assert stat.pss == 0


class TestTempStat:
    def test_create(self):
        stat = TempStat(cpu=35.5, gpu=36.0, skin=34.5, battery=35.0)
        assert stat.cpu == 35.5
        assert stat.gpu == 36.0

    def test_default(self):
        stat = TempStat()
        assert stat.cpu == 0.0


class TestFpsStat:
    def test_create(self):
        stat = FpsStat(fps=60.0, jank=2, big_jank=0)
        assert stat.fps == 60.0
        assert stat.jank == 2

    def test_default(self):
        stat = FpsStat()
        assert stat.fps == 0.0
