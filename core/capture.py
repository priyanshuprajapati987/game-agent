import numpy as np
from typing import Optional, Tuple

try:
    import dxcam
    HAS_DXCAM = True
except ImportError:
    HAS_DXCAM = False

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class ScreenCapture:
    def __init__(self, method: str = "auto", monitor: int = 0):
        self.method = method
        self.monitor = monitor
        self._dxcam_camera = None
        self._mss_instance = None
        self._init_capture()

    def _init_capture(self):
        if self.method == "auto":
            if HAS_DXCAM:
                self.method = "dxcam"
            elif HAS_MSS:
                self.method = "mss"
            else:
                raise RuntimeError("No capture library available. Install dxcam or mss.")

        if self.method == "dxcam":
            if not HAS_DXCAM:
                raise ImportError("dxcam not installed. Run: pip install dxcam")
            self._dxcam_camera = dxcam.create(output_color="BGR")
        elif self.method == "mss":
            if not HAS_MSS:
                raise ImportError("mss not installed. Run: pip install mss")
            self._mss_instance = mss.mss()

    def capture_region(
        self, left: int, top: int, width: int, height: int
    ) -> Optional[np.ndarray]:
        if self.method == "dxcam":
            return self._dxcam_region(left, top, width, height)
        elif self.method == "mss":
            return self._mss_region(left, top, width, height)
        return None

    def capture_full(self) -> Optional[np.ndarray]:
        if self.method == "dxcam":
            frame = self._dxcam_camera.grab()
            return frame
        elif self.method == "mss":
            monitor = self._mss_instance.monitors[self.monitor + 1]
            screenshot = self._mss_instance.grab(monitor)
            return np.array(screenshot)[:, :, :3]
        return None

    def capture_window(self, hwnd: int) -> Optional[np.ndarray]:
        if HAS_WIN32:
            try:
                rect = win32gui.GetClientRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]

                left, top = win32gui.ClientToScreen(hwnd, (0, 0))
                return self.capture_region(left, top, width, height)
            except Exception:
                return None
        return self.capture_full()

    def _dxcam_region(
        self, left: int, top: int, width: int, height: int
    ) -> Optional[np.ndarray]:
        region = (left, top, left + width, top + height)
        frame = self._dxcam_camera.grab(region=region)
        return frame

    def _mss_region(
        self, left: int, top: int, width: int, height: int
    ) -> Optional[np.ndarray]:
        region = {"left": left, "top": top, "width": width, "height": height}
        screenshot = self._mss_instance.grab(region)
        return np.array(screenshot)[:, :, :3]

    def set_monitor(self, monitor: int):
        self.monitor = monitor

    def release(self):
        if self._dxcam_camera:
            try:
                self._dxcam_camera.stop()
            except Exception:
                pass
        if self._mss_instance:
            self._mss_instance.close()
