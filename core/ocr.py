import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass

try:
    from paddleocr import PaddleOCR
    HAS_PADDLE = True
except ImportError:
    HAS_PADDLE = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


@dataclass
class OCRResult:
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2


class OCREngine:
    def __init__(self, lang: str = "en"):
        self.lang = lang
        self._ocr = None
        self._init_ocr()

    def _init_ocr(self):
        if HAS_PADDLE:
            self._ocr = PaddleOCR(use_angle_cls=True, lang=self.lang, show_log=False)
        else:
            raise ImportError("PaddleOCR not installed. Run: pip install paddleocr")

    def read_text(
        self,
        screen: np.ndarray,
        roi: Optional[Tuple[int, int, int, int]] = None,
    ) -> List[OCRResult]:
        if roi:
            x, y, w, h = roi
            screen = screen[y : y + h, x : x + w]
            offset_x, offset_y = x, y
        else:
            offset_x, offset_y = 0, 0

        processed = self._preprocess(screen)
        results = self._ocr.ocr(processed, cls=True)

        ocr_results = []
        if results and results[0]:
            for line in results[0]:
                box = line[0]
                text = line[1][0]
                confidence = float(line[1][1])

                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                x_min, x_max = int(min(xs)), int(max(xs))
                y_min, y_max = int(min(ys)), int(max(ys))

                ocr_results.append(
                    OCRResult(
                        text=text,
                        confidence=confidence,
                        x=x_min + offset_x,
                        y=y_min + offset_y,
                        width=x_max - x_min,
                        height=y_max - y_min,
                    )
                )

        return ocr_results

    def find_text(
        self,
        screen: np.ndarray,
        target_text: str,
        roi: Optional[Tuple[int, int, int, int]] = None,
        case_sensitive: bool = False,
    ) -> Optional[OCRResult]:
        results = self.read_text(screen, roi)
        for result in results:
            actual = result.text if case_sensitive else result.text.lower()
            target = target_text if case_sensitive else target_text.lower()
            if target in actual:
                return result
        return None

    def read_number(
        self,
        screen: np.ndarray,
        roi: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[float]:
        results = self.read_text(screen, roi)
        import re
        for result in results:
            cleaned = re.sub(r"[^\d.]", "", result.text)
            try:
                return float(cleaned)
            except ValueError:
                continue
        return None

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        if not HAS_CV2:
            return image

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        upscaled = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        blurred = cv2.GaussianBlur(upscaled, (3, 3), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary
