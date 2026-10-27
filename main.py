#****************#
# Mã sinh viên: [MÃ_SINH_VIÊN]
# Họ tên: [HỌ_TÊN]
#****************#
"""Demo kịch bản phòng học."""
import sys

from device_events import (AirConditionerRemote, AlertSeverity, ConsoleNotificationService,
                           DeviceAuditLogger, DeviceMonitoringCoordinator, DeviceStatus,
                           FilteredAlertSubscriber, InvalidDeviceReadingException,
                           MaintenanceService, ProjectorRemote, WirelessMicrophone)


def main() -> None:
    projector = ProjectorRemote("PRJ-01", "Máy chiếu P.301")
    ac = AirConditionerRemote("AC-01", "Điều hòa P.301", "P.301")
    mic = WirelessMicrophone("MIC-01", "Micro P.301")

    notifier, logger, maintenance = ConsoleNotificationService(), DeviceAuditLogger(), MaintenanceService()

    with DeviceMonitoringCoordinator([projector, ac, mic], notifier, logger, maintenance) as coordinator:
        coordinator.subscribe()

        # Subscriber bổ sung bằng lambda - KHÔNG sửa lớp thiết bị.
        critical_only = FilteredAlertSubscriber(
            lambda a: a.severity == AlertSeverity.CRITICAL,
            lambda a: print(f"CRITICAL: {a.device_id} - {a.message}"))
        for d in (projector, ac, mic):
            d.alert_raised += critical_only.handle_alert

        projector.change_status(DeviceStatus.BORROWED)
        projector.change_status(DeviceStatus.BORROWED)  # trùng -> không có event
        projector.update_battery_level(50)               # vùng an toàn -> không cảnh báo
        projector.update_battery_level(15)               # Warning
        projector.update_battery_level(10)               # cùng vùng -> không cảnh báo
        projector.update_battery_level(0)                # Critical

        ac.update_response_state(False)                  # Critical
        ac.update_response_state(False)                  # không lặp lại

        mic.update_battery_level(25)                     # Warning
        mic.update_signal_quality(35)                    # Warning
        mic.update_signal_quality(0)                     # Critical

        try:
            mic.update_battery_level(150)
        except InvalidDeviceReadingException as ex:
            print(f"Lỗi dữ liệu: {ex.device_id}, giá trị {ex.invalid_value}: {ex}")

        projector.change_status(DeviceStatus.UNDER_MAINTENANCE)

        # Thử tự phát sinh event từ bên ngoài -> không có phương thức invoke
        try:
            projector.alert_raised.invoke(projector, None)
        except AttributeError:
            print("Mã bên ngoài không thể tự phát sinh event (không có invoke).")

    print("\n-- Audit log --")
    for entry in logger.entries:
        print(entry)
    print("\n-- Yêu cầu bảo trì --")
    for req in maintenance.requests:
        print(req)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
