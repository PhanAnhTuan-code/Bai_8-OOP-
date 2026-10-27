#****************#
# Mã sinh viên: [MÃ_SINH_VIÊN]
# Họ tên: [HỌ_TÊN]
#****************#
"""Enum, lớp dữ liệu sự kiện và ngoại lệ."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum


class DeviceStatus(Enum):
    """Trạng thái thiết bị."""
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    UNDER_MAINTENANCE = "UnderMaintenance"

    def __str__(self) -> str:
        return self.value


class AlertSeverity(IntEnum):
    """Mức cảnh báo. IntEnum nên so sánh được: INFORMATION < WARNING < CRITICAL."""
    INFORMATION = 0
    WARNING = 1
    CRITICAL = 2

    def __str__(self) -> str:
        return self.name.capitalize()


@dataclass(frozen=True)
class DeviceStatusChangedEventArgs:
    """Dữ liệu sự kiện đổi trạng thái (frozen => bất biến)."""
    device_id: str
    old_status: DeviceStatus
    new_status: DeviceStatus
    changed_at: datetime


@dataclass(frozen=True)
class DeviceAlertEventArgs:
    """Dữ liệu sự kiện cảnh báo (frozen => bất biến)."""
    device_id: str
    message: str
    severity: AlertSeverity
    occurred_at: datetime


class InvalidDeviceReadingException(Exception):
    """Giá trị pin/tín hiệu nằm ngoài khoảng 0-100."""

    def __init__(self, device_id: str, invalid_value: int, message: str):
        super().__init__(message)
        self.device_id = device_id
        self.invalid_value = invalid_value
