#****************#
# Mã sinh viên: [MÃ_SINH_VIÊN]
# Họ tên: [HỌ_TÊN]
#****************#
"""Kiểm thử tự động (unittest)."""
import unittest

from device_events import (AirConditionerRemote, AlertSeverity, ConsoleNotificationService,
                           DeviceAuditLogger, DeviceMonitoringCoordinator, DeviceStatus,
                           FilteredAlertSubscriber, InvalidDeviceReadingException,
                           MaintenanceService, ProjectorRemote, WirelessMicrophone)


def capture(device):
    alerts = []
    device.alert_raised += lambda s, e: alerts.append(e)
    return alerts


class TeachingDeviceTests(unittest.TestCase):
    def test_same_status_no_event(self):
        d, n = ProjectorRemote("T1", "T1"), []
        d.status_changed += lambda s, e: n.append(e)
        d.change_status(DeviceStatus.AVAILABLE)
        self.assertEqual(n, [])

    def test_status_change_event_data_and_order(self):
        d, seen = ProjectorRemote("T1", "T1"), []
        d.status_changed += lambda s, e: seen.append((e, s.status))
        d.change_status(DeviceStatus.BORROWED)
        self.assertEqual(len(seen), 1)
        e, status_in_handler = seen[0]
        self.assertEqual((e.old_status, e.new_status, e.device_id),
                         (DeviceStatus.AVAILABLE, DeviceStatus.BORROWED, "T1"))
        self.assertEqual(status_in_handler, DeviceStatus.BORROWED)  # đã cập nhật trước khi phát

    def test_multiple_subscribers(self):
        d, a, b = ProjectorRemote("T2", "T2"), [], []
        d.status_changed += lambda s, e: a.append(1)
        d.status_changed += lambda s, e: b.append(1)
        d.change_status(DeviceStatus.BORROWED)
        self.assertEqual((len(a), len(b)), (1, 1))

    def test_outside_cannot_raise_event(self):
        d = ProjectorRemote("T3", "T3")
        self.assertFalse(hasattr(d.alert_raised, "invoke"))
        with self.assertRaises(AttributeError):
            d.alert_raised = None  # không được gán đè event

    def test_unsubscribe(self):
        d, n = ProjectorRemote("T4", "T4"), []
        h = lambda s, e: n.append(e)
        d.status_changed += h
        d.status_changed -= h
        d.change_status(DeviceStatus.BORROWED)
        self.assertEqual(n, [])


class ProjectorTests(unittest.TestCase):
    def test_battery_zones(self):
        p = ProjectorRemote("PRJ", "PRJ"); a = capture(p)
        p.update_battery_level(50);  self.assertEqual(len(a), 0)
        p.update_battery_level(19);  self.assertEqual([x.severity for x in a], [AlertSeverity.WARNING])
        p.update_battery_level(10);  self.assertEqual(len(a), 1)          # cùng vùng
        p.update_battery_level(0);   self.assertEqual(a[-1].severity, AlertSeverity.CRITICAL)
        p.update_battery_level(0);   self.assertEqual(len(a), 2)          # không lặp

    def test_exactly_20_no_alert(self):
        p = ProjectorRemote("P20", "P20"); a = capture(p)
        p.update_battery_level(20)
        self.assertEqual(a, [])

    def test_invalid_reading(self):
        p = ProjectorRemote("PB", "PB", 60); a = capture(p)
        for bad in (101, -1):
            with self.assertRaises(InvalidDeviceReadingException) as cm:
                p.update_battery_level(bad)
            self.assertEqual((cm.exception.device_id, cm.exception.invalid_value), ("PB", bad))
        self.assertEqual((p.battery_level, a), (60, []))


class AirConditionerTests(unittest.TestCase):
    def test_responsive_transitions(self):
        ac = AirConditionerRemote("AC", "AC", "P.101"); a = capture(ac)
        ac.update_response_state(True);  self.assertEqual(len(a), 0)
        ac.update_response_state(False)
        self.assertEqual([x.severity for x in a], [AlertSeverity.CRITICAL])
        ac.update_response_state(False); self.assertEqual(len(a), 1)      # không lặp
        ac.update_response_state(True)
        ac.update_response_state(False); self.assertEqual(len(a), 2)      # mất lại -> cảnh báo lại


class MicrophoneTests(unittest.TestCase):
    def test_zones(self):
        m = WirelessMicrophone("MIC", "MIC"); a = capture(m)
        m.update_battery_level(29);   self.assertEqual(a[-1].severity, AlertSeverity.WARNING)
        m.update_signal_quality(39);  self.assertEqual(a[-1].severity, AlertSeverity.WARNING)
        m.update_signal_quality(0);   self.assertEqual(a[-1].severity, AlertSeverity.CRITICAL)
        m.update_battery_level(0);    self.assertEqual(a[-1].severity, AlertSeverity.CRITICAL)
        self.assertEqual(len(a), 4)

    def test_invalid_signal(self):
        m = WirelessMicrophone("MIC", "MIC")
        with self.assertRaises(InvalidDeviceReadingException) as cm:
            m.update_signal_quality(200)
        self.assertEqual(cm.exception.invalid_value, 200)


class SubscriberTests(unittest.TestCase):
    def test_maintenance_only_critical(self):
        mt, m = MaintenanceService(), WirelessMicrophone("MIC3", "MIC3")
        m.alert_raised += mt.handle_critical_alert
        m.update_battery_level(10); self.assertEqual(len(mt.requests), 0)
        m.update_battery_level(0);  self.assertEqual(len(mt.requests), 1)

    def test_audit_logger(self):
        lg, d = DeviceAuditLogger(), ProjectorRemote("P", "P")
        d.status_changed += lg.handle_status_changed
        d.change_status(DeviceStatus.UNDER_MAINTENANCE)
        self.assertEqual(len(lg.entries), 1)
        self.assertIn("Available -> UnderMaintenance", lg.entries[0])

    def test_filtered_subscriber(self):
        got = []
        f = FilteredAlertSubscriber(lambda a: a.severity == AlertSeverity.CRITICAL,
                                    lambda a: got.append(a.device_id))
        m = WirelessMicrophone("MIC4", "MIC4")
        m.alert_raised += f.handle_alert
        m.update_battery_level(10); m.update_battery_level(0)
        self.assertEqual(got, ["MIC4"])


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.d, self.log = ProjectorRemote("C1", "C1"), DeviceAuditLogger()
        self.c = DeviceMonitoringCoordinator([self.d], ConsoleNotificationService(),
                                             self.log, MaintenanceService())

    def test_no_duplicate_subscribe(self):
        self.c.subscribe(); self.c.subscribe()
        self.d.change_status(DeviceStatus.BORROWED)
        self.assertEqual(len(self.log.entries), 1)

    def test_unsubscribe_and_resubscribe(self):
        self.c.subscribe(); self.d.change_status(DeviceStatus.BORROWED)
        self.c.unsubscribe(); self.d.change_status(DeviceStatus.AVAILABLE)
        self.assertEqual(len(self.log.entries), 1)
        self.c.subscribe(); self.d.change_status(DeviceStatus.BORROWED)
        self.assertEqual(len(self.log.entries), 2)

    def test_dispose_and_with(self):
        self.c.subscribe(); self.c.dispose()
        self.d.change_status(DeviceStatus.BORROWED)
        self.assertEqual(len(self.log.entries), 0)
        with self.c as cc:
            cc.subscribe()
            self.d.change_status(DeviceStatus.AVAILABLE)
        self.d.change_status(DeviceStatus.BORROWED)
        self.assertEqual(len(self.log.entries), 1)


if __name__ == "__main__":
    unittest.main()
