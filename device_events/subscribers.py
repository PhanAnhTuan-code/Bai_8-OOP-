#****************#
# Mã sinh viên: [MÃ_SINH_VIÊN]
# Họ tên: [HỌ_TÊN]
#****************#
"""Các subscriber."""
from typing import Any, Callable, List

from .models import AlertSeverity, DeviceAlertEventArgs, DeviceStatusChangedEventArgs

# Delegate tự định nghĩa: chính sách lọc cảnh báo (True = xử lý).
AlertFilter = Callable[[DeviceAlertEventArgs], bool]


class ConsoleNotificationService:
    """Hiển thị cảnh báo ra console."""

    def handle_alert(self, sender: Any, e: DeviceAlertEventArgs) -> None:
        print(f"[{e.severity}] {e.device_id}: {e.message}")


class DeviceAuditLogger:
    """Ghi lịch sử đổi trạng thái."""

    def __init__(self) -> None:
        self._entries: List[str] = []

    @property
    def entries(self) -> tuple:  # tuple => chỉ đọc
        return tuple(self._entries)

    def handle_status_changed(self, sender: Any, e: DeviceStatusChangedEventArgs) -> None:
        self._entries.append(
            f"{e.changed_at:%Y-%m-%d %H:%M:%S}: {e.device_id}, {e.old_status} -> {e.new_status}")


class MaintenanceService:
    """Tạo yêu cầu bảo trì khi có cảnh báo Critical."""

    def __init__(self) -> None:
        self._requests: List[str] = []

    @property
    def requests(self) -> tuple:
        return tuple(self._requests)

    def handle_critical_alert(self, sender: Any, e: DeviceAlertEventArgs) -> None:
        if e.severity != AlertSeverity.CRITICAL:
            return  # chỉ quan tâm lỗi nghiêm trọng
        self._requests.append(f"Maintenance request for {e.device_id}: {e.message}")


class FilteredAlertSubscriber:
    """Subscriber dùng callback: chỉ gọi action khi filter trả về True."""

    def __init__(self, alert_filter: AlertFilter,
                 action: Callable[[DeviceAlertEventArgs], None]) -> None:
        if alert_filter is None or action is None:
            raise ValueError("filter và action không được là None")
        self._filter = alert_filter
        self._action = action

    def handle_alert(self, sender: Any, e: DeviceAlertEventArgs) -> None:
        if self._filter(e):
            self._action(e)
