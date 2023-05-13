import enum
import typing

from .plugins.pm import PMMixin

if typing.TYPE_CHECKING:
    from adbc.adbclient import ADBClient


class Status(enum.Enum):
    DEVICE = "device"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class Device(PMMixin):
    def __init__(self, adbc: "ADBClient", serialno: str) -> None:
        self.adbc = adbc
        self.serialno = serialno
