# ============================================================
#  core/predictor.py
#  Load model và predict trạng thái mắt / miệng
#
#  FIX: dùng preprocess_input() của MobileNetV2 (scale [-1, 1])
#  thay vì /255 thủ công – phải khớp đúng với lúc training.
# ============================================================

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from dataclasses import dataclass
from typing import Optional

from config import (
    EYE_MODEL_PATH, MOUTH_MODEL_PATH,
    EYE_CONF_THRESHOLD, MOUTH_CONF_THRESHOLD,
    IMG_SIZE,
)


@dataclass
class EyePrediction:
    label: str        # "open" | "closed"
    prob_closed: float  # xác suất raw từ sigmoid [0,1]
    is_closed: bool


@dataclass
class MouthPrediction:
    label: str        # "yawn" | "no_yawn"
    prob_yawn: float  # xác suất raw từ sigmoid [0,1]
    is_yawning: bool


class Predictor:
    """
    Load 2 model MobileNetV2 và thực hiện predict realtime.

    Input ảnh phải là numpy uint8 (H, W, 3) BGR hoặc RGB –
    hàm này tự lo preprocess_input đúng chuẩn MobileNetV2.
    KHÔNG normalize thủ công trước khi truyền vào.
    """

    def __init__(self):
        print("[Predictor] Đang tải Eye Model...")
        self._eye_model = tf.keras.models.load_model(EYE_MODEL_PATH)

        print("[Predictor] Đang tải Mouth Model...")
        self._mouth_model = tf.keras.models.load_model(MOUTH_MODEL_PATH)

        # Warm-up: giảm latency frame đầu
        dummy_raw = np.zeros((1, *IMG_SIZE, 3), dtype=np.uint8)
        dummy_processed = preprocess_input(dummy_raw.astype(np.float32))
        self._eye_model.predict(dummy_processed, verbose=0)
        self._mouth_model.predict(dummy_processed, verbose=0)
        print("[Predictor] ✓ Cả 2 model đã sẵn sàng.\n")

    def _preprocess(self, img_rgb: np.ndarray) -> np.ndarray:
        """
        img_rgb: uint8 (H, W, 3) RGB hoặc float32 [0,1].
        Trả về float32 (1, 224, 224, 3) theo chuẩn MobileNetV2 [-1, 1].
        """
        # Resize nếu cần
        if img_rgb.shape[:2] != IMG_SIZE:
            import cv2
            img_rgb = cv2.resize(img_rgb, IMG_SIZE)

        # Nếu ảnh đã là float [0,1] → scale lại về [0,255] trước
        if img_rgb.dtype != np.uint8:
            img_rgb = (img_rgb * 255).astype(np.float32)
        else:
            img_rgb = img_rgb.astype(np.float32)

        # preprocess_input: scale về [-1, 1] (chuẩn MobileNetV2)
        batch = np.expand_dims(img_rgb, axis=0)  # (1, 224, 224, 3)
        return preprocess_input(batch)

    def predict_eye(self, img: Optional[np.ndarray]) -> EyePrediction:
        """
        img: RGB uint8 (224,224,3) — crop từ eye_extractor.
        Trả về EyePrediction.
        """
        if img is None:
            return EyePrediction(label="open", prob_closed=0.0, is_closed=False)

        batch = self._preprocess(img)
        prob_closed = float(self._eye_model.predict(batch, verbose=0)[0][0])

        is_closed = prob_closed >= EYE_CONF_THRESHOLD
        label = "closed" if is_closed else "open"
        return EyePrediction(label=label, prob_closed=prob_closed, is_closed=is_closed)

    def predict_mouth(self, img: Optional[np.ndarray]) -> MouthPrediction:
        """
        img: RGB uint8 (224,224,3) — crop từ mouth_extractor.
        Trả về MouthPrediction.
        """
        if img is None:
            return MouthPrediction(label="no_yawn", prob_yawn=0.0, is_yawning=False)

        batch = self._preprocess(img)
        prob_yawn = float(self._mouth_model.predict(batch, verbose=0)[0][0])

        is_yawning = prob_yawn >= MOUTH_CONF_THRESHOLD
        label = "yawn" if is_yawning else "no_yawn"
        return MouthPrediction(label=label, prob_yawn=prob_yawn, is_yawning=is_yawning)
