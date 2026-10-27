#****************#
# Mã sinh viên: [MÃ_SINH_VIÊN]
# Họ tên: [HỌ_TÊN]
#****************#
"""Điều phối đăng ký/hủy đăng ký event tại một nơi duy nhất."""
from typing import Iterable

from .devices import TeachingDevice
from .subscribers import ConsoleNotificationService, DeviceAuditLogger, MaintenanceService


class DeviceMonitoringCoordinator:
    """Hỗ trợ `with` (tương đương IDisposable): thoát khối sẽ tự Unsubscribe."""

    def __init__(self, devices: Iterable[TeachingDevice],
                 notification_service: ConsoleNotificationService,
                 audit_logger: DeviceAuditLogger,
                 maintenance_service: MaintenanceService) -> None:
        self._devices = list(devices)
        self._notification = notification_service
        self._audit = audit_logger
        self._maintenance = maintenance_service
        self._is_subscribed = False  # chống đăng ký trùng

    def subscribe(self) -> None:
        if self._is_subscribed:
            return
        for d in self._devices:
            d.status_changed += self._audit.handle_status_changed
            d.alert_raised += self._notification.handle_alert
            d.alert_raised += self._maintenance.handle_critical_alert
        self._is_subscribed = True

    def unsubscribe(self) -> None:
        if not self._is_subscribed:
            return
        for d in self._devices:
            d.status_changed -= self._audit.handle_status_changed
            d.alert_raised -= self._notification.handle_alert
            d.alert_raised -= self._maintenance.handle_critical_alert
        self._is_subscribed = False

    def dispose(self) -> None:
        self.unsubscribe()

    def __enter__(self) -> "DeviceMonitoringCoordinator":
        return self

    def __exit__(self, *exc) -> None:
        self.dispose()
