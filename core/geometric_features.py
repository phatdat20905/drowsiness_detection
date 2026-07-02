# ============================================================
#  core/geometric_features.py
#  Trích xuất đặc trưng hình học từ MediaPipe landmarks:
#  EAR, MAR, Blink Rate, Yawn Count, Head Pose.
#
#  Logic và ngưỡng được port 1:1 từ test2.py (nguồn tham chiếu),
#  đồng bộ tên biến/landmark index với config.py.
#
#  Các đặc trưng này KHÔNG thay thế model deep learning — chúng
#  được dùng làm tín hiệu hỗ trợ / fusion / lớp cảnh báo bổ sung
#  (xem core/fusion.py và core/alert_score.py).
# ============================================================

import time
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

from config import (
    L_OUTER, L_INNER, L_UPPER_1, L_LOWER_1, L_UPPER_2, L_LOWER_2,
    R_OUTER, R_INNER, R_UPPER_1, R_LOWER_1, R_UPPER_2, R_LOWER_2,
    P_LEFT, P_RIGHT, P_UPPER_1, P_LOWER_1, P_UPPER_2, P_LOWER_2,
    P_UPPER_3, P_LOWER_3,
    NOSE, HEAD_TOP, CHIN,
    EAR_THRESHOLD, EYE_CLOSED_FRAMES, BLINK_MAX_FRAMES, BLINK_RATE_THRESHOLD,
    MAR_THRESHOLD, YAWN_FRAMES, DISTRACTED_FRAMES,
    HEAD_HORIZONTAL_RIGHT, HEAD_HORIZONTAL_LEFT,
    HEAD_VERTICAL_UP, HEAD_VERTICAL_DOWN,
)


# ── Hàm tính toán cơ bản (giữ nguyên công thức từ test2.py) ───

def compute_distance(p1, p2) -> float:
    return float(np.linalg.norm(np.array(p1) - np.array(p2)))


def calculate_ear(landmarks, outer, inner, u1, l1, u2, l2) -> float:
    """Eye Aspect Ratio – công thức gốc từ test2.py."""
    v1 = compute_distance([landmarks[u1].x, landmarks[u1].y],
                          [landmarks[l1].x, landmarks[l1].y])
    v2 = compute_distance([landmarks[u2].x, landmarks[u2].y],
                          [landmarks[l2].x, landmarks[l2].y])
    h = compute_distance([landmarks[outer].x, landmarks[outer].y],
                         [landmarks[inner].x, landmarks[inner].y])
    return (v1 + v2) / (2.0 * h)


def calculate_mar(landmarks) -> float:
    """Mouth Aspect Ratio – công thức gốc từ test2.py."""
    d1 = compute_distance([landmarks[P_UPPER_1].x, landmarks[P_UPPER_1].y],
                          [landmarks[P_LOWER_1].x, landmarks[P_LOWER_1].y])
    d2 = compute_distance([landmarks[P_UPPER_2].x, landmarks[P_UPPER_2].y],
                          [landmarks[P_LOWER_2].x, landmarks[P_LOWER_2].y])
    d3 = compute_distance([landmarks[P_UPPER_3].x, landmarks[P_UPPER_3].y],
                          [landmarks[P_LOWER_3].x, landmarks[P_LOWER_3].y])
    h = compute_distance([landmarks[P_LEFT].x, landmarks[P_LEFT].y],
                         [landmarks[P_RIGHT].x, landmarks[P_RIGHT].y])
    return (d1 + d2 + d3) / (2.0 * h)


def estimate_head_pose(landmarks) -> str:
    """Ước lượng hướng nhìn dựa trên tỷ lệ khoảng cách hình học."""
    nose_p  = np.array([landmarks[NOSE].x, landmarks[NOSE].y])
    left_p  = np.array([landmarks[L_OUTER].x, landmarks[L_OUTER].y])
    right_p = np.array([landmarks[R_OUTER].x, landmarks[R_OUTER].y])
    top_p   = np.array([landmarks[HEAD_TOP].x, landmarks[HEAD_TOP].y])
    chin_p  = np.array([landmarks[CHIN].x, landmarks[CHIN].y])

    dist_left  = np.linalg.norm(nose_p - left_p)
    dist_right = np.linalg.norm(nose_p - right_p)
    horizontal_ratio = dist_left / (dist_right + 1e-6)

    dist_top  = np.linalg.norm(nose_p - top_p)
    dist_chin = np.linalg.norm(nose_p - chin_p)
    vertical_ratio = dist_top / (dist_chin + 1e-6)

    pose = "Nhin thang"
    if horizontal_ratio < HEAD_HORIZONTAL_RIGHT:
        pose = "Quay phai"
    elif horizontal_ratio > HEAD_HORIZONTAL_LEFT:
        pose = "Quay trai"
    elif vertical_ratio < HEAD_VERTICAL_UP:
        pose = "Nhin len"
    elif vertical_ratio > HEAD_VERTICAL_DOWN:
        pose = "Guc dau"

    return pose


def calculate_avg_ear(landmarks) -> float:
    """EAR trung bình 2 mắt – dùng landmark index đồng bộ config.py."""
    left_ear = calculate_ear(landmarks, L_OUTER, L_INNER,
                             L_UPPER_1, L_LOWER_1, L_UPPER_2, L_LOWER_2)
    right_ear = calculate_ear(landmarks, R_OUTER, R_INNER,
                              R_UPPER_1, R_LOWER_1, R_UPPER_2, R_LOWER_2)
    return (left_ear + right_ear) / 2.0


# ── Dataclass kết quả ───────────────────────────────────────────

@dataclass
class GeometricFeatures:
    """Snapshot toàn bộ đặc trưng hình học tại 1 frame."""
    avg_ear: float
    mar: float
    head_pose: str

    eye_closed_geo: bool        # EAR < threshold VÀ đủ frame liên tục
    mouth_yawn_geo: bool        # MAR > threshold VÀ đủ frame liên tục
    is_distracted: bool         # head pose lệch đủ lâu

    blink_rate: int             # lần/phút
    yawn_count_total: int       # tổng số lần ngáp từ đầu phiên
    is_fatigue_blink: bool      # blink_rate vượt ngưỡng (mỏi mắt sớm)

    eye_counter: int            # frame nhắm mắt liên tục hiện tại
    yawn_counter: int           # frame đang ngáp liên tục hiện tại
    distracted_counter: int     # frame mất tập trung liên tục hiện tại


class GeometricFeatureExtractor:
    """
    Bộ trích xuất đặc trưng hình học có trạng thái (stateful),
    port nguyên logic từ test2.py thành class tái sử dụng được
    trong pipeline real-time / Streamlit / Tkinter.

    Cách dùng:
        extractor = GeometricFeatureExtractor()
        ...
        for frame in stream:
            landmarks = face_mesh_result.multi_face_landmarks[0].landmark
            feats = extractor.update(landmarks)
    """

    def __init__(self):
        self.eye_counter         = 0
        self.yawn_counter        = 0
        self.yawn_count_total    = 0
        self.distracted_counter  = 0
        self.blink_timestamps: List[float] = []

    def reset(self):
        self.__init__()

    def update(self, landmarks) -> GeometricFeatures:
        """
        Tính toàn bộ đặc trưng cho 1 frame.
        landmarks: face_landmarks.landmark (list mediapipe NormalizedLandmark)
        """
        current_time = time.time()

        # Dọn blink timestamps cũ hơn 60 giây
        self.blink_timestamps = [
            t for t in self.blink_timestamps if current_time - t <= 60
        ]
        blink_rate = len(self.blink_timestamps)

        avg_ear   = calculate_avg_ear(landmarks)
        mar       = calculate_mar(landmarks)
        head_pose = estimate_head_pose(landmarks)

        # ── 1. EAR → trạng thái mắt nhắm (geometric) ──────────
        eye_closed_geo = False
        if avg_ear < EAR_THRESHOLD:
            self.eye_counter += 1
            if self.eye_counter >= EYE_CLOSED_FRAMES:
                eye_closed_geo = True
        else:
            # Nháy mắt bình thường (ngắn) → ghi nhận blink
            if 0 < self.eye_counter < BLINK_MAX_FRAMES:
                self.blink_timestamps.append(current_time)
            self.eye_counter = 0

        # ── 2. Blink rate → mỏi mắt sớm ───────────────────────
        is_fatigue_blink = blink_rate >= BLINK_RATE_THRESHOLD

        # ── 3. Head pose → mất tập trung ──────────────────────
        is_distracted = False
        if head_pose != "Nhin thang":
            self.distracted_counter += 1
            if self.distracted_counter >= DISTRACTED_FRAMES:
                is_distracted = True
        else:
            self.distracted_counter = 0

        # ── 4. MAR → ngáp (geometric) ─────────────────────────
        mouth_yawn_geo = False
        if mar > MAR_THRESHOLD:
            self.yawn_counter += 1
            if self.yawn_counter == YAWN_FRAMES:
                self.yawn_count_total += 1
            if self.yawn_counter >= YAWN_FRAMES:
                mouth_yawn_geo = True
        else:
            self.yawn_counter = 0

        return GeometricFeatures(
            avg_ear           = avg_ear,
            mar                = mar,
            head_pose          = head_pose,
            eye_closed_geo     = eye_closed_geo,
            mouth_yawn_geo     = mouth_yawn_geo,
            is_distracted      = is_distracted,
            blink_rate         = blink_rate,
            yawn_count_total   = self.yawn_count_total,
            is_fatigue_blink   = is_fatigue_blink,
            eye_counter        = self.eye_counter,
            yawn_counter       = self.yawn_counter,
            distracted_counter = self.distracted_counter,
        )
