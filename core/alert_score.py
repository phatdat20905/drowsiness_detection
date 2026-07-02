# ============================================================
#  core/alert_score.py
#  Tính Alert Score và phân loại Normal / Tired / Drowsy.
#
#  MỞ RỘNG: nhận thêm GeometricFeatures để tính penalty bổ sung
#  từ head pose (mất tập trung) và blink rate (mỏi mắt sớm).
# ============================================================

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

from config import (
    ALERT_SCORE_MAX,
    CLOSED_CONSEC_FRAMES, CLOSED_PENALTY_PER_FRAME,
    YAWN_WINDOW_SEC, YAWN_PENALTY_PER_COUNT,
    SCORE_RECOVERY_RATE,
    DISTRACTION_PENALTY_PER_FRAME,
    FATIGUE_BLINK_PENALTY,
    TIRED_THRESHOLD, DROWSY_THRESHOLD,
)


class DrowsinessStatus:
    NORMAL = "NORMAL"
    TIRED  = "TIRED"
    DROWSY = "DROWSY"


@dataclass
class AlertState:
    score: float
    status: str
    # CNN/Fusion counters
    closed_consec_frames: int
    yawn_count_in_window: int
    total_closed_count: int
    total_yawn_count: int
    total_warning_count: int
    # Geometric extras (hiển thị thêm trên UI)
    blink_rate: int
    yawn_count_geo: int
    head_pose: str
    is_distracted: bool
    is_fatigue_blink: bool
    ear: float
    mar: float


class AlertScoreEngine:
    """
    Nhận quyết định fusion (is_closed, is_yawning) + đặc trưng
    hình học (GeometricFeatures) → tính Alert Score → phân loại.

    Nguồn penalty:
      1. Mắt nhắm liên tục (từ fusion)        → -CLOSED_PENALTY/frame
      2. Ngáp trong cửa sổ 60s (từ fusion)   → penalty tuyến tính
      3. Mất tập trung / gục đầu (geometric) → -DISTRACTION_PENALTY/frame
      4. Blink rate cao – mỏi mắt sớm (geo)  → -FATIGUE_BLINK/frame
    """

    def __init__(self):
        self._score: float = float(ALERT_SCORE_MAX)
        self._closed_consec: int = 0
        self._yawn_active: bool  = False
        self._yawn_timestamps: Deque[float] = deque()
        self._total_closed_count:  int = 0
        self._total_yawn_count:    int = 0
        self._total_warning_count: int = 0
        self._prev_status: str = DrowsinessStatus.NORMAL

    def update(
        self,
        is_closed: bool,
        is_yawning: bool,
        geo=None,          # Optional[GeometricFeatures]
    ) -> AlertState:
        """
        Gọi mỗi frame sau fusion.
        geo: GeometricFeatures hoặc None (khi không detect được mặt).
        """
        now = time.time()

        # ── 1. Penalty mắt nhắm ───────────────────────────────
        if is_closed:
            self._closed_consec += 1
            if self._closed_consec == 1:
                self._total_closed_count += 1
            if self._closed_consec >= CLOSED_CONSEC_FRAMES:
                self._score -= CLOSED_PENALTY_PER_FRAME
        else:
            self._closed_consec = 0

        # ── 2. Penalty ngáp ───────────────────────────────────
        if is_yawning and not self._yawn_active:
            self._yawn_active = True
            self._yawn_timestamps.append(now)
            self._total_yawn_count += 1
        elif not is_yawning:
            self._yawn_active = False

        while self._yawn_timestamps and (now - self._yawn_timestamps[0]) > YAWN_WINDOW_SEC:
            self._yawn_timestamps.popleft()

        yawn_in_window = len(self._yawn_timestamps)

        if is_yawning:
            scale = min(yawn_in_window / 3.0, 1.0)
            self._score -= (YAWN_PENALTY_PER_COUNT / 30.0) * scale

        # ── 3. Penalty geometric bổ sung ─────────────────────
        blink_rate    = 0
        yawn_count_geo = 0
        head_pose     = "N/A"
        is_distracted = False
        is_fatigue    = False
        ear_val       = 0.0
        mar_val       = 0.0

        if geo is not None:
            blink_rate     = geo.blink_rate
            yawn_count_geo = geo.yawn_count_total
            head_pose      = geo.head_pose
            is_distracted  = geo.is_distracted
            is_fatigue     = geo.is_fatigue_blink
            ear_val        = geo.avg_ear
            mar_val        = geo.mar

            # Mất tập trung (head pose lệch đủ lâu)
            if is_distracted:
                self._score -= DISTRACTION_PENALTY_PER_FRAME

            # Mỏi mắt sớm (blink rate vượt ngưỡng)
            if is_fatigue:
                self._score -= FATIGUE_BLINK_PENALTY

        # ── 4. Hồi phục khi bình thường ──────────────────────
        if not is_closed and not is_yawning and not is_distracted:
            self._score += SCORE_RECOVERY_RATE

        # ── 5. Clamp [0, 100] ─────────────────────────────────
        self._score = max(0.0, min(float(ALERT_SCORE_MAX), self._score))

        # ── 6. Phân loại ──────────────────────────────────────
        status = self._classify()
        if status == DrowsinessStatus.DROWSY and self._prev_status != DrowsinessStatus.DROWSY:
            self._total_warning_count += 1
        self._prev_status = status

        return AlertState(
            score                = round(self._score, 1),
            status               = status,
            closed_consec_frames = self._closed_consec,
            yawn_count_in_window = yawn_in_window,
            total_closed_count   = self._total_closed_count,
            total_yawn_count     = self._total_yawn_count,
            total_warning_count  = self._total_warning_count,
            blink_rate           = blink_rate,
            yawn_count_geo       = yawn_count_geo,
            head_pose            = head_pose,
            is_distracted        = is_distracted,
            is_fatigue_blink     = is_fatigue,
            ear                  = round(ear_val, 3),
            mar                  = round(mar_val, 3),
        )

    def reset(self):
        self.__init__()

    @property
    def score(self) -> float:
        return self._score

    def _classify(self) -> str:
        if self._score >= TIRED_THRESHOLD:
            return DrowsinessStatus.NORMAL
        elif self._score >= DROWSY_THRESHOLD:
            return DrowsinessStatus.TIRED
        else:
            return DrowsinessStatus.DROWSY
