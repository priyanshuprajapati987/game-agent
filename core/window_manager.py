from typing import Optional, List, Tuple
from dataclasses import dataclass

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


@dataclass
class WindowInfo:
    hwnd: int
    title: str
    class_name: str
    rect: Tuple[int, int, int, int]
    width: int = 0
    height: int = 0

    def __post_init__(self):
        self.width = self.rect[2] - self.rect[0]
        self.height = self.rect[3] - self.rect[1]


class WindowManager:
    def __init__(self):
        if not HAS_WIN32:
            raise ImportError("pywin32 not installed. Run: pip install pywin32")

    def find_window(self, title: str, exact: bool = False) -> Optional[WindowInfo]:
        results = []

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if exact:
                    if window_title == title:
                        results.append(hwnd)
                else:
                    if title.lower() in window_title.lower():
                        results.append(hwnd)

        win32gui.EnumWindows(enum_callback, None)

        if results:
            return self._get_window_info(results[0])
        return None

    def find_window_by_class(self, class_name: str) -> Optional[WindowInfo]:
        hwnd = win32gui.FindWindow(class_name, None)
        if hwnd:
            return self._get_window_info(hwnd)
        return None

    def find_windows_by_title(self, partial_title: str) -> List[WindowInfo]:
        results = []

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if partial_title.lower() in window_title.lower():
                    results.append(hwnd)

        win32gui.EnumWindows(enum_callback, None)
        return [self._get_window_info(hwnd) for hwnd in results]

    def get_foreground_window(self) -> Optional[WindowInfo]:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            return self._get_window_info(hwnd)
        return None

    def set_foreground(self, hwnd: int) -> bool:
        try:
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return True
            except Exception:
                return False

    def get_client_rect(self, hwnd: int) -> Tuple[int, int, int, int]:
        rect = win32gui.GetClientRect(hwnd)
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))
        return (left, top, rect[2], rect[3])

    def get_window_rect(self, hwnd: int) -> Tuple[int, int, int, int]:
        return win32gui.GetWindowRect(hwnd)

    def minimize_window(self, hwnd: int):
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

    def maximize_window(self, hwnd: int):
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

    def restore_window(self, hwnd: int):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    def is_window_visible(self, hwnd: int) -> bool:
        return win32gui.IsWindowVisible(hwnd)

    def _get_window_info(self, hwnd: int) -> WindowInfo:
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        return WindowInfo(hwnd=hwnd, title=title, class_name=class_name, rect=rect)

    def get_all_windows(self) -> List[WindowInfo]:
        windows = []

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append(self._get_window_info(hwnd))

        win32gui.EnumWindows(enum_callback, None)
        return windows
