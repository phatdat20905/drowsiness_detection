# ============================================================
#  core/eye_extractor.py
#  Crop vùng mắt từ FaceResult → RGB uint8 cho Predictor.
#
#  FIX: trả về uint8 (không /255) vì predictor.py tự gọi
#  preprocess_input() để khớp đúng chuẩn MobileNetV2.
# ============================================================

import cv2
import numpy as np
from typing import Optional, Tuple

from core.face_detector import FaceResult
from config import LEFT_EYE_LANDMARKS, RIGHT_EYE_LANDMARKS, EYE_PADDING, IMG_SIZE


def extract_eye_region(
    frame: np.ndarray,
    face: FaceResult,
    use_both_eyes: bool = True,
) -> Optional[np.ndarray]:
    """
    Crop và resize vùng mắt từ frame.
    Returns: RGB uint8 (224, 224, 3), hoặc None nếu crop lỗi.
    """
    indices = (LEFT_EYE_LANDMARKS + RIGHT_EYE_LANDMARKS
               if use_both_eyes else LEFT_EYE_LANDMARKS)
    try:
        x1, y1, x2, y2 = face.get_bounding_box(indices, padding=EYE_PADDING)
        if x2 <= x1 or y2 <= y1:
            return None
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0 or crop.shape[0] < 5 or crop.shape[1] < 5:
            return None
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        return cv2.resize(crop_rgb, IMG_SIZE)   # uint8, NO /255
    except Exception:
        return None


def get_eye_bbox(face: FaceResult) -> Tuple[int, int, int, int]:
    indices = LEFT_EYE_LANDMARKS + RIGHT_EYE_LANDMARKS
    return face.get_bounding_box(indices, padding=EYE_PADDING)

def get_left_eye_bbox(face: FaceResult):
    return face.get_bounding_box(
        LEFT_EYE_LANDMARKS,
        padding=EYE_PADDING
    )

def get_right_eye_bbox(face: FaceResult):
    return face.get_bounding_box(
        RIGHT_EYE_LANDMARKS,
        padding=EYE_PADDING
    )