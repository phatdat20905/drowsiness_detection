# views/monitor_page.py  –  Trang giám sát tài xế (real-time)
import streamlit as st
import cv2
import time
import numpy as np
from datetime import datetime
from PIL import Image

from components.styles import inject_css, section_header, page_header
from database.db import (
    start_session, end_session, insert_alert, get_recent_alerts,
)


def render():
    inject_css()
    user = st.session_state.user
    uid  = user["id"]

    page_header("📷 Giám sát thời gian thực",
                "Camera phát hiện buồn ngủ · CNN + MediaPipe Fusion")

    # ── Session state ──────────────────────────────────────────
    if "monitoring" not in st.session_state:
        st.session_state.monitoring = False
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "mon_stats" not in st.session_state:
        st.session_state.mon_stats = {
            "min_score": 100.0, "closed": 0,
            "yawn": 0, "warnings": 0,
        }

    # ── Import core modules (lazy – chỉ khi user nhấn Start) ──
    def _load_modules():
        """Load nặng chỉ 1 lần vào session cache."""
        if "dms_modules" not in st.session_state:
            try:
                import sys
                from pathlib import Path

                ROOT_DIR = Path(__file__).resolve().parents[2]
                sys.path.insert(0, str(ROOT_DIR))
                from core.face_detector      import FaceDetector
                from core.eye_extractor      import extract_eye_region, get_eye_bbox
                from core.mouth_extractor    import extract_mouth_region, get_mouth_bbox
                from core.predictor          import Predictor
                from core.geometric_features import GeometricFeatureExtractor
                from core.fusion             import fuse, FusionResult
                from core.alert_score        import AlertScoreEngine, DrowsinessStatus
                from core.alarm              import AlarmSystem
                import mediapipe as mp

                st.session_state.dms_modules = {
                    "detector":    FaceDetector(),
                    "predictor":   Predictor(),
                    "geo_extract": GeometricFeatureExtractor(),
                    "engine":      AlertScoreEngine(),
                    "alarm":       AlarmSystem(),
                    "face_mesh":   mp.solutions.face_mesh.FaceMesh(
                        max_num_faces=1, refine_landmarks=True,
                        min_detection_confidence=0.5, min_tracking_confidence=0.5,
                    ),
                    "fuse":             fuse,
                    "FusionResult":     FusionResult,
                    "DrowsinessStatus": DrowsinessStatus,
                    "extract_eye":      extract_eye_region,
                    "extract_mouth":    extract_mouth_region,
                    "get_eye_bbox":     get_eye_bbox,
                    "get_mouth_bbox":   get_mouth_bbox,
                }
                return True, ""
            except Exception as e:
                return False, str(e)
        return True, ""

    # ── Layout ────────────────────────────────────────────────
    col_cam, col_dash = st.columns([3, 2], gap="large")

    with col_cam:
        # Start / Stop buttons
        bc1, bc2 = st.columns(2)
        with bc1:
            start_btn = st.button(
                "▶  Bắt đầu giám sát",
                disabled=st.session_state.monitoring,
                use_container_width=True, type="primary",
            )
        with bc2:
            stop_btn = st.button(
                "⏹  Dừng",
                disabled=not st.session_state.monitoring,
                use_container_width=True,
            )

        # Camera frame placeholder
        cam_placeholder = st.empty()
        status_placeholder = st.empty()

        if not st.session_state.monitoring:
            cam_placeholder.markdown("""
            <div class="cam-placeholder">
                <div class="cam-icon">📷</div>
                <div style="font-size:14px;">Nhấn <b>Bắt đầu giám sát</b> để mở camera</div>
                <div style="font-size:12px;color:#484f58;">Webcam sẽ được kích hoạt tự động</div>
            </div>""", unsafe_allow_html=True)

    with col_dash:
        section_header("Trạng thái")
        score_ph  = st.empty()
        status_ph = st.empty()
        info_ph   = st.empty()
        warn_ph   = st.empty()

        section_header("Phiên hiện tại")
        stats_ph  = st.empty()

    # ── Start ─────────────────────────────────────────────────
    if start_btn:
        ok, err = _load_modules()
        if not ok:
            st.error(f"Không thể load model: {err}\n\nHãy chạy training trước.")
            st.stop()
        st.session_state.monitoring = True
        st.session_state.session_id = start_session(uid)
        st.session_state.mon_stats  = {
            "min_score": 100.0, "closed": 0, "yawn": 0, "warnings": 0,
        }
        st.rerun()

    # ── Stop ──────────────────────────────────────────────────
    if stop_btn and st.session_state.monitoring:
        st.session_state.monitoring = False
        s = st.session_state.mon_stats
        if st.session_state.session_id:
            end_session(st.session_state.session_id,
                        s["min_score"], s["closed"], s["yawn"], s["warnings"])
        st.session_state.session_id = None
        st.rerun()

    # ── Monitoring loop ───────────────────────────────────────
    if st.session_state.monitoring and "dms_modules" in st.session_state:
        m   = st.session_state.dms_modules
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            st.error("Không thể mở webcam!")
            st.session_state.monitoring = False
            st.rerun()

        import mediapipe as mp

        DrowsinessStatus = m["DrowsinessStatus"]
        null_fusion = m["FusionResult"](
            "open", 0.0, False, "no_yawn", 0.0, False, 0.0, 0.0, 0.0, 0.0
        )
        last_state = m["engine"].update(False, False)
        prev_t = time.time()
        stats  = st.session_state.mon_stats

        try:
            while st.session_state.monitoring:
                # Flush buffer
                for _ in range(2):
                    cap.grab()
                ret, frame = cap.retrieve()
                if not ret:
                    break

                now = time.time()
                fps = 1.0 / max(now - prev_t, 1e-9)
                prev_t = now

                face = m["detector"].detect(frame)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                mesh_res = m["face_mesh"].process(rgb)
                rgb.flags.writeable = True

                fusion = null_fusion
                state  = last_state

                if face is not None and mesh_res.multi_face_landmarks:
                    landmarks = mesh_res.multi_face_landmarks[0].landmark
                    geo       = m["geo_extract"].update(landmarks)

                    eye_img   = m["extract_eye"](frame, face)
                    mouth_img = m["extract_mouth"](frame, face)
                    eye_pred   = m["predictor"].predict_eye(eye_img)
                    mouth_pred = m["predictor"].predict_mouth(mouth_img)
                    fusion     = m["fuse"](eye_pred, mouth_pred, geo)
                    state      = m["engine"].update(
                        fusion.is_closed, fusion.is_yawning, geo
                    )
                    last_state = state

                    # Update stats
                    if state.score < stats["min_score"]:
                        stats["min_score"] = state.score
                    stats["closed"]   = state.total_closed_count
                    stats["yawn"]     = state.total_yawn_count
                    stats["warnings"] = state.total_warning_count

                    # Draw ROI
                    ex1, ey1, ex2, ey2 = m["get_eye_bbox"](face)
                    mx1, my1, mx2, my2 = m["get_mouth_bbox"](face)
                    cv2.rectangle(frame, (ex1, ey1), (ex2, ey2), (0, 255, 255), 1)
                    cv2.rectangle(frame, (mx1, my1), (mx2, my2), (255, 128, 0), 1)

                    # Log alert to DB
                    if state.status in ("TIRED", "DROWSY"):
                        if m["alarm"].trigger() or True:   # log every TIRED/DROWSY
                            insert_alert(
                                uid, st.session_state.session_id,
                                state.status, state.score,
                                state.ear, state.mar, state.blink_rate,
                                state.head_pose,
                                fusion.cnn_prob_eye, fusion.cnn_prob_mouth,
                                fusion.eye_prob_fused, fusion.mouth_prob_fused,
                            )

                # ── Overlay trên frame ─────────────────────────
                score_val = state.score
                if score_val >= 70:
                    sc_color = (0, 200, 0)
                elif score_val >= 40:
                    sc_color = (0, 165, 255)
                else:
                    sc_color = (0, 0, 220)

                h, w = frame.shape[:2]
                cv2.rectangle(frame, (0, 0), (w, 5), (40, 40, 40), -1)
                cv2.rectangle(frame, (0, 0), (int(w * score_val / 100), 5), sc_color, -1)

                lbl = f"{state.status}  Score:{score_val:.0f}  FPS:{fps:.0f}"
                cv2.putText(frame, lbl, (10, 34),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, sc_color, 2)

                # ── Show frame ────────────────────────────────
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                cam_placeholder.image(frame_rgb, channels="RGB",
                                      use_container_width=True)

                # ── Dashboard panels ──────────────────────────
                sc_class = (
                    "score-normal" if score_val >= 70 else
                    "score-tired"  if score_val >= 40 else
                    "score-drowsy"
                )
                score_ph.markdown(f"""
                <div class="score-container">
                    <div style="display:flex;justify-content:space-between;
                                font-size:12px;color:#8b949e;margin-bottom:6px;">
                        <span>Alert Score</span><span>{score_val:.0f}/100</span>
                    </div>
                    <div class="score-bar-bg">
                        <div class="score-bar-fill {sc_class}"
                             style="width:{score_val}%"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

                badge_map = {
                    "NORMAL": ("badge-normal", "✅"),
                    "TIRED":  ("badge-tired",  "⚠️"),
                    "DROWSY": ("badge-drowsy",  "🚨"),
                }
                bc, bi = badge_map.get(state.status, ("badge-normal", "✅"))
                status_ph.markdown(
                    f'<span class="badge {bc}" style="font-size:1.1rem;padding:8px 18px;">'
                    f'{bi} {state.status}</span>',
                    unsafe_allow_html=True,
                )

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
                info_ph.markdown(f"""
                <div style="
                    font-family:'JetBrains Mono',monospace;
                    font-size:12px;
                    color:#8b949e;
                    line-height:2;
                    margin-top:10px;
                ">
                👁️ Eye: <b style="color:#e6edf3">{fusion.eye_label.upper()}</b> ({eye_conf:.0%})<br>
                👄 Mouth: <b style="color:#e6edf3">{fusion.mouth_label.upper()}</b> ({mouth_conf:.0%})<br>
                📐 EAR: {state.ear:.3f} &nbsp; MAR: {state.mar:.3f}<br>
                👀 Blink: {state.blink_rate}/min<br>
                🧭 Pose: {state.head_pose}
                </div>
                """, unsafe_allow_html=True)
                if state.status == "DROWSY":
                    warn_ph.markdown("""
                    <div class="alert-drowsy">
                        <span style="font-size:1.4rem;">🚨</span>
                        <div>
                            <b style="color:#f85149;">BUỒN NGỦ NGUY HIỂM</b><br>
                            <span style="font-size:12px;color:#8b949e;">Dừng xe và nghỉ ngơi ngay!</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
                elif state.status == "TIRED":
                    warn_ph.markdown("""
                    <div class="alert-tired">
                        ⚠️ <b style="color:#d29922;">Đang mệt mỏi</b> —
                        <span style="font-size:12px;color:#8b949e;">Hãy nghỉ ngơi sớm.</span>
                    </div>""", unsafe_allow_html=True)
                else:
                    warn_ph.markdown("""
                    <div style="color:#3fb950;font-size:13px;padding:8px 0;">
                        ✅ Trạng thái bình thường
                    </div>""", unsafe_allow_html=True)

                stats_ph.markdown(f"""
                <div style="font-size:13px;color:#8b949e;line-height:2.2;">
                    😴 Nhắm mắt &nbsp;&nbsp;: <b>{stats['closed']}</b><br>
                    🥱 Ngáp &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: <b>{stats['yawn']}</b><br>
                    🚨 Cảnh báo &nbsp;: <b>{stats['warnings']}</b><br>
                    📉 Score thấp : <b>{stats['min_score']:.1f}</b>
                </div>""", unsafe_allow_html=True)

        finally:
            cap.release()

    # ── Recent alerts ─────────────────────────────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    section_header("Lịch sử cảnh báo gần nhất")

    rows = get_recent_alerts(user_id=uid, limit=20, days=7)
    if rows:
        import pandas as pd
        df = pd.DataFrame(
            [dict(r) for r in rows],
            columns=["timestamp", "status", "score", "ear", "mar",
                     "blink_rate", "head_pose"],
        )
        df["status"] = df["status"].map({
            "TIRED":  "⚠️ TIRED",
            "DROWSY": "🚨 DROWSY",
            "NORMAL": "✅ NORMAL",
        })
        st.dataframe(df, use_container_width=True, height=220)
    else:
        st.info("Chưa có cảnh báo trong 7 ngày qua.")
