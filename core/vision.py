import cv2
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MatchResult:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    center_x: int = 0
    center_y: int = 0

    def __post_init__(self):
        self.center_x = self.x + self.width // 2
        self.center_y = self.y + self.height // 2


class VisionEngine:
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        self._templates: dict[str, np.ndarray] = {}

    def load_template(self, name: str, path: str) -> bool:
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            return False
        self._templates[name] = img
        return True

    def load_templates_from_dir(self, directory: str):
        dir_path = Path(directory)
        for img_path in dir_path.glob("*.png"):
            self.load_template(img_path.stem, str(img_path))
        for img_path in dir_path.glob("*.jpg"):
            self.load_template(img_path.stem, str(img_path))

    def find_template(
        self,
        screen: np.ndarray,
        template_name: str,
        confidence: Optional[float] = None,
    ) -> Optional[MatchResult]:
        if template_name not in self._templates:
            return None

        template = self._templates[template_name]
        return self._match(screen, template, confidence)

    def find_all_templates(
        self,
        screen: np.ndarray,
        template_name: str,
        confidence: Optional[float] = None,
        max_results: int = 10,
    ) -> List[MatchResult]:
        if template_name not in self._templates:
            return []

        template = self._templates[template_name]
        return self._match_all(screen, template, confidence, max_results)

    def find_in_region(
        self,
        screen: np.ndarray,
        template_name: str,
        roi: Tuple[int, int, int, int],
        confidence: Optional[float] = None,
    ) -> Optional[MatchResult]:
        x, y, w, h = roi
        region = screen[y : y + h, x : x + w]
        result = self._match(region, self._templates.get(template_name), confidence)
        if result:
            result.x += x
            result.y += y
            result.center_x += x
            result.center_y += y
        return result

    def check_pixel_color(
        self,
        screen: np.ndarray,
        x: int,
        y: int,
        target_color: Tuple[int, int, int],
        tolerance: int = 30,
    ) -> bool:
        if y >= screen.shape[0] or x >= screen.shape[1]:
            return False
        pixel = screen[y, x]
        return all(abs(int(pixel[i]) - target_color[i]) <= tolerance for i in range(3))

    def check_region_color(
        self,
        screen: np.ndarray,
        roi: Tuple[int, int, int, int],
        target_color: Tuple[int, int, int],
        tolerance: int = 30,
        threshold: float = 0.5,
    ) -> bool:
        x, y, w, h = roi
        region = screen[y : y + h, x : x + w]
        mask = np.all(np.abs(region.astype(int) - np.array(target_color)) <= tolerance, axis=2)
        return np.mean(mask) >= threshold

    def get_brightness(self, screen: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> float:
        if roi:
            x, y, w, h = roi
            region = screen[y : y + h, x : x + w]
        else:
            region = screen
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))

    def preprocess_for_matching(self, image: np.ndarray, scale: float = 1.0) -> np.ndarray:
        if scale != 1.0:
            image = cv2.resize(image, None, fx=scale, fy=scale)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.equalizeHist(gray)

    def _match(
        self,
        screen: np.ndarray,
        template: np.ndarray,
        confidence: Optional[float] = None,
    ) -> Optional[MatchResult]:
        if template is None:
            return None

        thresh = confidence or self.confidence_threshold
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= thresh:
            h, w = template.shape[:2]
            return MatchResult(
                x=max_loc[0],
                y=max_loc[1],
                width=w,
                height=h,
                confidence=max_val,
            )
        return None

    def _match_all(
        self,
        screen: np.ndarray,
        template: np.ndarray,
        confidence: Optional[float] = None,
        max_results: int = 10,
    ) -> List[MatchResult]:
        if template is None:
            return []

        thresh = confidence or self.confidence_threshold
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= thresh)

        matches = []
        h, w = template.shape[:2]

        for pt in zip(*locations[::-1]):
            match = MatchResult(
                x=pt[0],
                y=pt[1],
                width=w,
                height=h,
                confidence=float(result[pt[1], pt[0]]),
            )
            if self._is_unique(match, matches):
                matches.append(match)
                if len(matches) >= max_results:
                    break

        return matches

    def _is_unique(self, match: MatchResult, existing: List[MatchResult], min_distance: int = 20) -> bool:
        for e in existing:
            if abs(match.x - e.x) < min_distance and abs(match.y - e.y) < min_distance:
                return False
        return True
