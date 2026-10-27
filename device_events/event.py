#****************#
# Mã sinh viên: [MÃ_SINH_VIÊN]
# Họ tên: [HỌ_TÊN]
#****************#
"""Cơ chế event/delegate tự cài đặt (Python không có từ khóa event).

- Event            : giữ danh sách handler và có invoke(); CHỈ publisher giữ đối tượng này.
- EventSubscription: "cửa sổ" công khai chỉ cho += / -=, KHÔNG có invoke().
Nhờ vậy mã bên ngoài đăng ký/hủy được nhưng không tự phát sinh event.
"""
from typing import Any, Callable, List

Handler = Callable[[Any, Any], None]  # delegate dạng (sender, args) -> None


class Event:
    def __init__(self) -> None:
        self._handlers: List[Handler] = []
        self.subscription = EventSubscription(self)

    def invoke(self, sender: Any, args: Any) -> None:
        # Duyệt trên bản sao: handler đăng ký/hủy giữa chừng không làm hỏng vòng lặp.
        for handler in list(self._handlers):
            handler(sender, args)


class EventSubscription:
    def __init__(self, event: Event) -> None:
        self._event = event

    def add(self, handler: Handler) -> None:
        self._event._handlers.append(handler)

    def remove(self, handler: Handler) -> None:
        # Giống C#: hủy handler không tồn tại thì bỏ qua.
        if handler in self._event._handlers:
            self._event._handlers.remove(handler)

    def __iadd__(self, handler: Handler) -> "EventSubscription":
        self.add(handler)
        return self

    def __isub__(self, handler: Handler) -> "EventSubscription":
        self.remove(handler)
        return self

    def __len__(self) -> int:
        return len(self._event._handlers)
