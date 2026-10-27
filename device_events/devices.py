#****************#
# Mã sinh viên: [MÃ_SINH_VIÊN]
# Họ tên: [HỌ_TÊN]
#****************#
"""Publisher: TeachingDevice và các thiết bị cụ thể."""
from abc import ABC
from datetime import datetime

from .event import Event, EventSubscription
from .models import (AlertSeverity, DeviceAlertEventArgs, DeviceStatus,
                     DeviceStatusChangedEventArgs, InvalidDeviceReadingException)


class TeachingDevice(ABC):
    """Lớp trừu tượng - PUBLISHER. Chỉ phát hiện và công bố; không biết ai lắng nghe."""

    def __init__(self, device_id: str, name: str) -> None:
        self._id = device_id
        self._name = name
        self._status = DeviceStatus.AVAILABLE
        # Event thật: private, chỉ lớp này và lớp dẫn xuất được invoke.
        self._status_changed = Event()
        self._alert_raised = Event()

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> DeviceStatus:  # chỉ đọc từ bên ngoài (private set)
        return self._status

    # --- Phần công khai của event: chỉ += và -= ---
    @property
    def status_changed(self) -> EventSubscription:
        return self._status_changed.subscription

    @status_changed.setter
    def status_changed(self, value: EventSubscription) -> None:
        # Cho phép cú pháp `d.status_changed += h` (Python gán lại sau __iadd__),
        # nhưng từ chối gán đối tượng khác.
        if value is not self._status_changed.subscription:
            raise AttributeError("Không thể gán trực tiếp event; chỉ dùng += hoặc -=.")

    @property
    def alert_raised(self) -> EventSubscription:
        return self._alert_raised.subscription

    @alert_raised.setter
    def alert_raised(self, value: EventSubscription) -> None:
        if value is not self._alert_raised.subscription:
            raise AttributeError("Không thể gán trực tiếp event; chỉ dùng += hoặc -=.")

    def change_status(self, new_status: DeviceStatus) -> None:
        """Không phát event nếu trùng trạng thái; cập nhật status TRƯỚC khi phát event."""
        if new_status == self._status:
            return
        old_status = self._status
        self._status = new_status
        self._on_status_changed(DeviceStatusChangedEventArgs(
            self._id, old_status, new_status, datetime.now()))

    def _raise_alert(self, message: str, severity: AlertSeverity) -> None:
        self._on_alert_raised(DeviceAlertEventArgs(
            self._id, message, severity, datetime.now()))

    # Mẫu On...: lớp dẫn xuất có thể override để mở rộng.
    def _on_status_changed(self, e: DeviceStatusChangedEventArgs) -> None:
        self._status_changed.invoke(self, e)

    def _on_alert_raised(self, e: DeviceAlertEventArgs) -> None:
        self._alert_raised.invoke(self, e)

    def _validate_percent(self, value: int, what: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
            raise InvalidDeviceReadingException(
                self._id, value, f"{what} phải nằm trong khoảng 0-100 (nhận được {value}).")

    @staticmethod
    def _zone_of(value: int, warning_threshold: int) -> AlertSeverity:
        """0 => CRITICAL; dưới ngưỡng => WARNING; còn lại => INFORMATION (an toàn)."""
        if value == 0:
            return AlertSeverity.CRITICAL
        if value < warning_threshold:
            return AlertSeverity.WARNING
        return AlertSeverity.INFORMATION


class ProjectorRemote(TeachingDevice):
    """Pin <20% Warning; pin = 0% Critical."""
    _WARNING_THRESHOLD = 20

    def __init__(self, device_id: str, name: str, initial_battery: int = 100) -> None:
        super().__init__(device_id, name)
        self._validate_percent(initial_battery, "Mức pin")
        self._battery_level = initial_battery

    @property
    def battery_level(self) -> int:
        return self._battery_level

    def update_battery_level(self, new_level: int) -> None:
        self._validate_percent(new_level, "Mức pin")  # sai => ném lỗi, giữ nguyên trạng thái
        old_zone = self._zone_of(self._battery_level, self._WARNING_THRESHOLD)
        new_zone = self._zone_of(new_level, self._WARNING_THRESHOLD)
        self._battery_level = new_level
        # Chỉ cảnh báo khi RƠI sang vùng nghiêm trọng hơn => không lặp trong cùng vùng.
        if new_zone > old_zone:
            msg = ("Pin máy chiếu đã hết (0%)." if new_zone == AlertSeverity.CRITICAL
                   else f"Pin máy chiếu thấp ({new_level}%).")
            self._raise_alert(msg, new_zone)


class AirConditionerRemote(TeachingDevice):
    """Chuyển từ phản hồi -> không phản hồi: Critical (không lặp)."""

    def __init__(self, device_id: str, name: str, assigned_room: str) -> None:
        super().__init__(device_id, name)
        self._assigned_room = assigned_room
        self._is_responsive = True

    @property
    def assigned_room(self) -> str:
        return self._assigned_room

    @property
    def is_responsive(self) -> bool:
        return self._is_responsive

    def update_response_state(self, is_responsive: bool) -> None:
        was_responsive = self._is_responsive
        self._is_responsive = is_responsive
        if was_responsive and not is_responsive:
            self._raise_alert(f"Điều hòa phòng {self._assigned_room} không phản hồi.",
                              AlertSeverity.CRITICAL)


class WirelessMicrophone(TeachingDevice):
    """Pin <30% Warning; tín hiệu <40% Warning; pin hoặc tín hiệu = 0 Critical."""
    _BATTERY_WARNING = 30
    _SIGNAL_WARNING = 40

    def __init__(self, device_id: str, name: str,
                 initial_battery: int = 100, initial_signal: int = 100) -> None:
        super().__init__(device_id, name)
        self._validate_percent(initial_battery, "Mức pin")
        self._validate_percent(initial_signal, "Chất lượng tín hiệu")
        self._battery_level = initial_battery
        self._signal_quality = initial_signal

    @property
    def battery_level(self) -> int:
        return self._battery_level

    @property
    def signal_quality(self) -> int:
        return self._signal_quality

    def update_battery_level(self, new_level: int) -> None:
        self._validate_percent(new_level, "Mức pin")
        old_zone = self._zone_of(self._battery_level, self._BATTERY_WARNING)
        new_zone = self._zone_of(new_level, self._BATTERY_WARNING)
        self._battery_level = new_level
        if new_zone > old_zone:
            msg = ("Pin micro đã hết (0%)." if new_zone == AlertSeverity.CRITICAL
                   else f"Pin micro thấp ({new_level}%).")
            self._raise_alert(msg, new_zone)

    def update_signal_quality(self, new_quality: int) -> None:
        self._validate_percent(new_quality, "Chất lượng tín hiệu")
        old_zone = self._zone_of(self._signal_quality, self._SIGNAL_WARNING)
        new_zone = self._zone_of(new_quality, self._SIGNAL_WARNING)
        self._signal_quality = new_quality
        if new_zone > old_zone:
            msg = ("Micro mất tín hiệu (0%)." if new_zone == AlertSeverity.CRITICAL
                   else f"Chất lượng tín hiệu micro thấp ({new_quality}%).")
            self._raise_alert(msg, new_zone)
