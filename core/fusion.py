# ============================================================
#  core/fusion.py
#  Kết hợp xác suất từ CNN (model) với đặc trưng hình học
#  (EAR, MAR) để ra quyết định cuối cùng mỗi frame.
#
#  Nguyên tắc:
#   - Model deep learning (CNN) là nguồn quyết định chính.
#   - EAR/MAR là đặc trưng hỗ trợ: khi CNN không chắc (prob
#     gần 0.5), EAR/MAR bẻ về hướng rõ ràng hơn.
#   - Fusion: weighted average của CNN prob và geometric prob.
#   - Geometric "prob" = 1.0 nếu vượt ngưỡng, 0.0 nếu không.
#   - Không bao giờ dùng ngưỡng thủ công để thay thế model.
# ============================================================

from dataclasses import dataclass

from config import (
    FUSION_WEIGHT_CNN, FUSION_WEIGHT_GEO,
    EYE_CONF_THRESHOLD, MOUTH_CONF_THRESHOLD,
    EAR_THRESHOLD, MAR_THRESHOLD,
)
from core.predictor import EyePrediction, MouthPrediction
from core.geometric_features import GeometricFeatures


@dataclass
class FusionResult:
    """Kết quả sau fusion CNN + geometric."""
    # Mắt
    eye_label: str        # "open" | "closed"
    eye_prob_fused: float # xác suất "closed" sau fusion [0,1]
    is_closed: bool

    # Miệng
    mouth_label: str
    mouth_prob_fused: float  # xác suất "yawn" sau fusion [0,1]
    is_yawning: bool

    # Debug
    cnn_prob_eye: float
    cnn_prob_mouth: float
    geo_prob_eye: float
    geo_prob_mouth: float


def fuse(
    eye_pred: EyePrediction,
    mouth_pred: MouthPrediction,
    geo: GeometricFeatures,
) -> FusionResult:
    """
    Fusion weighted average:
      fused = w_cnn * p_cnn  +  w_geo * p_geo

    p_geo được tính liên tục (không nhị phân cứng) từ EAR/MAR:
      - Mắt: p_geo = 1 - clip(EAR / EAR_THRESHOLD, 0, 1)
        (EAR càng thấp so với ngưỡng → p_geo → 1)
      - Miệng: p_geo = clip(MAR / MAR_THRESHOLD - 1, 0, 1)
        (MAR càng cao so với ngưỡng → p_geo → 1)

    Cách tính này giúp geometric signal mượt và không nhảy cóc.
    """
    # ── Geometric probability (liên tục, không cứng 0/1) ──────
    # Mắt: EAR thấp → mắt nhắm → p_geo_eye cao
    geo_prob_eye = float(
        1.0 - min(geo.avg_ear / (EAR_THRESHOLD + 1e-6), 1.0)
    )

    # Miệng: MAR cao → ngáp → p_geo_mouth cao
    geo_prob_mouth = float(
        min(max(geo.mar / (MAR_THRESHOLD + 1e-6) - 1.0, 0.0), 1.0)
    )

    # ── Weighted fusion ───────────────────────────────────────
    fused_eye = (FUSION_WEIGHT_CNN * eye_pred.prob_closed
                 + FUSION_WEIGHT_GEO * geo_prob_eye)

    fused_mouth = (FUSION_WEIGHT_CNN * mouth_pred.prob_yawn
                   + FUSION_WEIGHT_GEO * geo_prob_mouth)

    # Clamp [0, 1]
    fused_eye   = max(0.0, min(1.0, fused_eye))
    fused_mouth = max(0.0, min(1.0, fused_mouth))

    # ── Ngưỡng quyết định cuối (dùng threshold CNN gốc) ───────
    is_closed   = fused_eye   >= EYE_CONF_THRESHOLD
    is_yawning  = fused_mouth >= MOUTH_CONF_THRESHOLD

    return FusionResult(
        eye_label        = "closed" if is_closed else "open",
        eye_prob_fused   = round(fused_eye, 4),
        is_closed        = is_closed,
        mouth_label      = "yawn" if is_yawning else "no_yawn",
        mouth_prob_fused = round(fused_mouth, 4),
        is_yawning       = is_yawning,
        cnn_prob_eye     = eye_pred.prob_closed,
        cnn_prob_mouth   = mouth_pred.prob_yawn,
        geo_prob_eye     = round(geo_prob_eye, 4),
        geo_prob_mouth   = round(geo_prob_mouth, 4),
    )
