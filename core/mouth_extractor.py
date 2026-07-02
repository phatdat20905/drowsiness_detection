# ============================================================
#  core/mouth_extractor.py
#  Crop vùng miệng từ FaceResult → RGB uint8 cho Predictor.
# ============================================================

import cv2
import numpy as np
from typing import Optional, Tuple

from core.face_detector import FaceResult
from config import MOUTH_LANDMARKS, MOUTH_PADDING, IMG_SIZE


def extract_mouth_region(
    frame: np.ndarray,
    face: FaceResult,
) -> Optional[np.ndarray]:
    """
    Crop và resize vùng miệng từ frame.
    Returns: RGB uint8 (224, 224, 3), hoặc None nếu crop lỗi.
    """
    try:
        x1, y1, x2, y2 = face.get_bounding_box(MOUTH_LANDMARKS, padding=MOUTH_PADDING)
        if x2 <= x1 or y2 <= y1:
            return None
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0 or crop.shape[0] < 5 or crop.shape[1] < 5:
            return None
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        return cv2.resize(crop_rgb, IMG_SIZE)   # uint8, NO /255
    except Exception:
        return None


def get_mouth_bbox(face: FaceResult) -> Tuple[int, int, int, int]:
    return face.get_bounding_box(MOUTH_LANDMARKS, padding=MOUTH_PADDING)
