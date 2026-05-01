from typing import List, Tuple, Union
from pydantic import BaseModel, Field


# ============ service/host.py 模型 ============
class DeviceStatusNotification(BaseModel):
    serialno: str
    status: Union[str, object]


class ForwardRule(BaseModel):
    serialno: str
    local: str
    remote: str


class ReverseRule(BaseModel):
    type: str
    local: str
    remote: str


# ============ plugins/fps.py 模型 ============
class FpsStat(BaseModel):
    fps: float = 0
    jank: float = 0
    big_jank: float = 0
    frametimes: List[float] = Field(default_factory=list)


# ============ plugins/cpu.py 模型 ============
class CPUInfo(BaseModel):
    platform: str
    name: str
    abi: str
    core: int
    freq: Tuple[int, int]


class CPUUsage(BaseModel):
    usage: float = Field(default=0.0)
    normalized: float = Field(default=0.0)


class CPUFreq(BaseModel):
    min: int = 0
    cur: int = 0
    max: int = 0


class CPUStat(BaseModel):
    user: float = 0
    nice: float = 0
    system: float = 0
    idle: float = 0
    iowait: float = 0
    irq: float = 0
    softirq: float = 0
    stealstolen: float = 0
    guest: float = 0
    guest_nice: float = 0

    @property
    def total(self):
        return (
            self.user
            + self.nice
            + self.system
            + self.idle
            + self.iowait
            + self.irq
            + self.softirq
            + self.stealstolen
            + self.guest
            + self.guest_nice
        )

    @property
    def total_idle(self):
        return self.idle + self.iowait

    @property
    def usage(self) -> float:
        return 100 * (self.total - self.total_idle) / self.total

    def __add__(self, other: "CPUStat"):
        summary = CPUStat()
        summary.user = self.user + other.user
        summary.nice = self.nice + other.nice
        summary.system = self.system + other.system
        summary.idle = self.idle + other.idle
        summary.iowait = self.iowait + other.iowait
        summary.irq = self.irq + other.irq
        summary.softirq = self.softirq + other.softirq
        summary.stealstolen = self.stealstolen + other.stealstolen
        summary.guest = self.guest + other.guest
        summary.guest_nice = self.guest_nice + other.guest_nice
        return summary

    def __sub__(self, other: "CPUStat"):
        result = CPUStat()
        result.user = self.user - other.user
        result.nice = self.nice - other.nice
        result.system = self.system - other.system
        result.idle = self.idle - other.idle
        result.iowait = self.iowait - other.iowait
        result.irq = self.irq - other.irq
        result.softirq = self.softirq - other.softirq
        result.stealstolen = self.stealstolen - other.stealstolen
        result.guest = self.guest - other.guest
        result.guest_nice = self.guest_nice - other.guest_nice
        return result

    def __str__(self):
        attrs = vars(self)
        return ", ".join("%s: %s" % item for item in attrs.items())


class ProcessCPUStat(BaseModel):
    name: str = ""
    utime: int = 0
    stime: int = 0
    cutime: int = 0
    cstime: int = 0

    def __add__(self, other: "ProcessCPUStat"):
        summary = ProcessCPUStat(name=self.name)
        summary.utime = self.utime + other.utime
        summary.stime = self.stime + other.stime
        summary.cutime = self.cutime + other.cutime
        summary.cstime = self.cstime + other.cstime
        return summary

    def __sub__(self, other: "ProcessCPUStat"):
        result = ProcessCPUStat(name=self.name)
        result.utime = self.utime - other.utime
        result.stime = self.stime - other.stime
        result.cutime = self.cutime - other.cutime
        result.cstime = self.cstime - other.cstime
        return result

    def __str__(self):
        attrs = vars(self)
        return ", ".join("%s: %s" % item for item in attrs.items())

    @property
    def total(self) -> float:
        return self.utime + self.stime + self.cutime + self.cstime


# ============ plugins/mem.py 模型 ============
class MemInfo(BaseModel):
    mem_total: int = 0
    swap_total: int = 0


class MemStat(BaseModel):
    pss: int = Field(default=0)
    private_dirty: int = Field(default=0)
    private_clean: int = Field(default=0)
    swapped_dirty: int = Field(default=0)
    heap_size: int = Field(default=0)
    heap_alloc: int = Field(default=0)
    heap_free: int = Field(default=0)


# ============ plugins/gpu.py 模型 ============
class GPUInfo(BaseModel):
    manufactor: str
    name: str
    opengl: str


# ============ plugins/battery.py 模型 ============
class BatteryStat(BaseModel):
    ac_powered: bool = Field(default=False)
    usb_powered: bool = Field(default=False)
    wireless_powered: bool = Field(default=False)
    max_charging_current: int = Field(default=-1)
    max_charging_voltage: int = Field(default=-1)
    charge_counter: int = Field(default=-1)
    status: int = Field(default=-1)
    health: int = Field(default=-1)
    present: bool = Field(default=False)
    level: int = Field(default=-1)
    scale: int = Field(default=-1)
    voltage: float = Field(default=-1)
    temperature: float = Field(default=-1)
    technology: str = Field(default="Unknown")


# ============ plugins/temp.py 模型 ============
class TempStat(BaseModel):
    cpu: float = 0.0
    gpu: float = 0.0
    skin: float = 0.0
    battery: float = 0.0


# ============ plugins/traffic.py 模型 ============
class TrafficStat(BaseModel):
    receive: float
    send: float

    def __sub__(self, other: "TrafficStat"):
        receive = self.receive - other.receive
        send = self.send - other.send
        return TrafficStat(receive=receive, send=send)

    def __add__(self, other: "TrafficStat"):
        receive = self.receive + other.receive
        send = self.send + other.send
        return TrafficStat(receive=receive, send=send)


# ============ plugins/wm.py 模型 ============
class Resolution(BaseModel):
    physical_size: str
    override_size: str
