# ============================================================
#  main.py  –  Real-time pipeline tích hợp đầy đủ:
#              CNN (MobileNetV2) + EAR/MAR/Blink/HeadPose fusion
#
#  Chạy: python main.py
#  Nhấn Q hoặc ESC để thoát, D để bật/tắt debug overlay.
# ============================================================

import cv2
import time
import csv
import os
import numpy as np
from datetime import datetime

from config import (
    FRAME_WIDTH, FRAME_HEIGHT, DISPLAY_FPS,
    COLOR_NORMAL, COLOR_TIRED, COLOR_DROWSY, COLOR_TEXT,
    TIRED_THRESHOLD, DROWSY_THRESHOLD,
    DAILY_STATS_CSV, ALERTS_CSV, LOGS_DIR,
    EAR_THRESHOLD, MAR_THRESHOLD,
)
from core.face_detector      import FaceDetector
from core.eye_extractor      import extract_eye_region, get_eye_bbox, get_left_eye_bbox, get_right_eye_bbox
from core.mouth_extractor    import extract_mouth_region, get_mouth_bbox
from core.predictor          import Predictor
from core.geometric_features import GeometricFeatureExtractor
from core.fusion             import fuse
from core.alert_score        import AlertScoreEngine, DrowsinessStatus, AlertState
from core.alarm              import AlarmSystem

import mediapipe as mp
_mp_face_mesh = mp.solutions.face_mesh


STATUS_COLORS = {
    DrowsinessStatus.NORMAL: COLOR_NORMAL,
    DrowsinessStatus.TIRED:  COLOR_TIRED,
    DrowsinessStatus.DROWSY: COLOR_DROWSY,
}


# ── Log helpers ───────────────────────────────────────────────

def init_logs():
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(DAILY_STATS_CSV):
        with open(DAILY_STATS_CSV, "w", newline="") as f:
            csv.writer(f).writerow([
                "date", "session_start", "session_end",
                "closed_count", "yawn_count_cnn",
                "yawn_count_geo", "warning_count", "min_score",
            ])
    if not os.path.exists(ALERTS_CSV):
        with open(ALERTS_CSV, "w", newline="") as f:
            csv.writer(f).writerow([
                "timestamp", "status", "score",
                "ear", "mar", "blink_rate", "head_pose",
                "cnn_prob_eye", "cnn_prob_mouth",
                "fused_eye", "fused_mouth",
            ])


def log_alert(state: AlertState, fusion):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ALERTS_CSV, "a", newline="") as f:
        csv.writer(f).writerow([
            ts, state.status, state.score,
            state.ear, state.mar, state.blink_rate, state.head_pose,
            fusion.cnn_prob_eye, fusion.cnn_prob_mouth,
            fusion.eye_prob_fused, fusion.mouth_prob_fused,
        ])


def log_session(session_start, state: AlertState, min_score):
    with open(DAILY_STATS_CSV, "a", newline="") as f:
        csv.writer(f).writerow([
            datetime.now().strftime("%Y-%m-%d"),
            session_start,
            datetime.now().strftime("%H:%M:%S"),
            state.total_closed_count,
            state.total_yawn_count,
            state.yawn_count_geo,
            state.total_warning_count,
            round(min_score, 1),
        ])


# ── Overlay ───────────────────────────────────────────────────

def draw_overlay(frame, state: AlertState, fusion, fps, face_found, debug):
    h, w = frame.shape[:2]
    color = STATUS_COLORS.get(state.status, COLOR_NORMAL)

    # ── Score bar ─────────────────────────────────────────────
    bar_w = int(w * state.score / 100)
    cv2.rectangle(frame, (0, 0), (w, 6), (40, 40, 40), -1)
    cv2.rectangle(frame, (0, 0), (bar_w, 6), color, -1)

    # ── Status + score ────────────────────────────────────────
    cv2.rectangle(frame, (0, 6), (w, 56), (20, 20, 40), -1)
    cv2.putText(frame,
                f"{state.status}   Score: {state.score:.0f}",
                (12, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 2)

    # ── Info strip bên phải ───────────────────────────────────
    panel_x = w - 220
    cv2.rectangle(frame, (panel_x, 60), (w, h), (20, 20, 40), -1)

    # Confidence theo nhãn đang hiển thị
    eye_conf = (
        fusion.eye_prob_fused
        if fusion.eye_label == "closed"
        else 1.0 - fusion.eye_prob_fused
    )

    mouth_conf = (
        fusion.mouth_prob_fused
        if fusion.mouth_label == "yawn"
        else 1.0 - fusion.mouth_prob_fused
    )

    lines = [
        f"Eye : {fusion.eye_label.upper()} {eye_conf:.0%}",
        f"Mouth:{fusion.mouth_label.upper()} {mouth_conf:.0%}",
        f"EAR : {state.ear:.3f}",
        f"MAR : {state.mar:.3f}",
        f"Blink:{state.blink_rate}/min",
        f"Pose: {state.head_pose}",
        f"Close:{state.total_closed_count}  Yawn:{state.total_yawn_count}",
        f"Warn :{state.total_warning_count}  FPS:{fps:.0f}",
    ]
    for i, line in enumerate(lines):
        clr = (0, 165, 255) if (
            (i == 0 and fusion.is_closed) or
            (i == 1 and fusion.is_yawning) or
            (i == 5 and state.is_distracted) or
            (i == 4 and state.is_fatigue_blink)
        ) else (200, 200, 200)
        cv2.putText(frame, line, (panel_x + 6, 85 + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, clr, 1)

    # ── Debug: CNN vs Geo prob ────────────────────────────────
    if debug and face_found:
        dbg = [
            f"CNN eye :{fusion.cnn_prob_eye:.3f}",
            f"Geo eye :{fusion.geo_prob_eye:.3f}",
            f"CNN mouth:{fusion.cnn_prob_mouth:.3f}",
            f"Geo mouth:{fusion.geo_prob_mouth:.3f}",
        ]
        for i, line in enumerate(dbg):
            cv2.putText(frame, line, (12, h - 80 + i * 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 255, 180), 1)

    # ── DROWSY full-screen warning ────────────────────────────
    if state.status == DrowsinessStatus.DROWSY:
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 56), (panel_x, h), (0, 0, 150), -1)
        cv2.addWeighted(overlay, 0.28, frame, 0.72, 0, frame)
        warn = "! BUON NGU - DUNG XE !"
        (tw, _), _ = cv2.getTextSize(warn, cv2.FONT_HERSHEY_SIMPLEX, 0.95, 2)
        cv2.putText(frame, warn, ((panel_x - tw) // 2, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.95, (50, 50, 255), 2)

    # ── Head pose / fatigue alerts ────────────────────────────
    if state.is_distracted:
        cv2.putText(frame,
                    f"MAT TAP TRUNG: {state.head_pose.upper()}",
                    (12, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                    (0, 165, 255), 2)
    elif state.is_fatigue_blink:
        cv2.putText(frame, "MOI MAT SOM (blink rate cao)",
                    (12, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 200, 255), 2)

    if not face_found:
        cv2.putText(frame, "Khong phat hien khuon mat",
                    (12, h // 2), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, (0, 165, 255), 2)
    return frame


# ── Main ──────────────────────────────────────────────────────

def run():
    init_logs()
    session_start = datetime.now().strftime("%H:%M:%S")
    min_score = 100.0
    debug_mode = False

    print("=" * 55)
    print("  Driver Drowsiness Detection  (CNN + MediaPipe Fusion)")
    print("  Q / ESC → thoát    D → bật/tắt debug overlay")
    print("=" * 55)

    # Khởi tạo tất cả modules
    detector    = FaceDetector()
    predictor   = Predictor()
    geo_extract = GeometricFeatureExtractor()
    engine      = AlertScoreEngine()
    alarm       = AlarmSystem()

    # MediaPipe FaceMesh riêng để lấy raw landmarks cho EAR/MAR
    face_mesh = _mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, DISPLAY_FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # tránh buffer stale frames

    if not cap.isOpened():
        print("[ERROR] Không thể mở webcam!")
        return

    prev_time = time.time()
    last_state = engine.update(False, False)
    from core.fusion import FusionResult
    from core.predictor import EyePrediction, MouthPrediction
    null_fusion = FusionResult("open", 0.0, False, "no_yawn", 0.0, False, 0.0, 0.0, 0.0, 0.0)

    try:
        while True:
            # Flush buffer: grab nhiều frame, chỉ decode frame cuối
            for _ in range(2):
                cap.grab()
            ret, frame = cap.retrieve()
            if not ret:
                print("[WARN] Không đọc được frame.")
                break

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-9)
            prev_time = now

            # ── Detect bằng FaceDetector (cho CNN crop) ────────
            face = detector.detect(frame)

            # ── Lấy raw landmarks cho geometric features ───────
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            mesh_results = face_mesh.process(rgb)
            rgb.flags.writeable = True

            geo = None
            fusion = null_fusion
            state  = last_state

            if face is not None and mesh_results.multi_face_landmarks:
                landmarks = mesh_results.multi_face_landmarks[0].landmark

                # ── Geometric features (EAR / MAR / pose) ──────
                geo = geo_extract.update(landmarks)

                # ── CNN predict ─────────────────────────────────
                eye_img   = extract_eye_region(frame, face)
                mouth_img = extract_mouth_region(frame, face)
                eye_pred   = predictor.predict_eye(eye_img)
                mouth_pred = predictor.predict_mouth(mouth_img)

                # ── Fusion ──────────────────────────────────────
                fusion = fuse(eye_pred, mouth_pred, geo)

                # ── Alert Score (fusion + geo penalty) ─────────
                state = engine.update(fusion.is_closed, fusion.is_yawning, geo)
                last_state = state

                if state.score < min_score:
                    min_score = state.score

                # ── Vẽ ROI boxes ────────────────────────────────
                ex1, ey1, ex2, ey2 = get_eye_bbox(face)
                cv2.rectangle(frame, (ex1, ey1), (ex2, ey2), (0, 255, 255), 1)
                # lex1, ley1, lex2, ley2 = get_left_eye_bbox(face)
                # rex1, rey1, rex2, rey2 = get_right_eye_bbox(face)
                # cv2.rectangle(
                #     frame,
                #     (lex1, ley1),
                #     (lex2, ley2),
                #     (0, 255, 255),
                #     1
                # )

                # cv2.rectangle(
                #     frame,
                #     (rex1, rey1),
                #     (rex2, rey2),
                #     (0, 255, 255),
                #     1
                # )
                mx1, my1, mx2, my2 = get_mouth_bbox(face)
                cv2.rectangle(frame, (mx1, my1), (mx2, my2), (255, 128, 0), 1)

                # ── Alarm ───────────────────────────────────────
                if state.status == DrowsinessStatus.DROWSY:
                    if alarm.trigger():
                        log_alert(state, fusion)

            frame = draw_overlay(frame, state, fusion, fps,
                                  face is not None, debug_mode)
            cv2.imshow("Driver Drowsiness Detection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
            elif key in (ord("d"), ord("D")):
                debug_mode = not debug_mode
                print(f"[Debug] {'ON' if debug_mode else 'OFF'}")

    finally:
        cap.release()
        face_mesh.close()
        cv2.destroyAllWindows()
        detector.close()
        alarm.stop()
        log_session(session_start, last_state, min_score)

        print("\n── Thống kê phiên ──────────────────────────────")
        print(f"  Nhắm mắt (CNN) : {last_state.total_closed_count}")
        print(f"  Ngáp (CNN)     : {last_state.total_yawn_count}")
        print(f"  Ngáp (Geo)     : {last_state.yawn_count_geo}")
        print(f"  Cảnh báo       : {last_state.total_warning_count}")
        print(f"  Điểm thấp nhất : {min_score:.1f}")
        print(f"  Log lưu tại    : {LOGS_DIR}")
        print("─────────────────────────────────────────────────")


if __name__ == "__main__":
    run()
