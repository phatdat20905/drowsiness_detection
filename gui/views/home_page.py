# views/home_page.py
import streamlit as st
from components.styles import inject_css, kpi_card
from database.db import get_kpi


def render():
    inject_css()
    user = st.session_state.get("user", {})
    role = user.get("role", "driver")

    # ── Hero ──────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#161b22 0%,#1c2333 100%);
                border:1px solid #30363d;border-radius:16px;
                padding:40px 40px 36px;margin-bottom:28px;position:relative;overflow:hidden;">
        <div style="position:absolute;right:-30px;top:-30px;
                    font-size:8rem;opacity:.05;transform:rotate(-10deg);">🚗</div>
        <div style="font-size:11px;font-weight:700;letter-spacing:.1em;
                    text-transform:uppercase;color:#2f81f7;margin-bottom:10px;">
            Driver Monitoring System
        </div>
        <h1 style="font-size:2rem;font-weight:700;color:#e6edf3;margin:0 0 10px;line-height:1.2;">
            Xin chào, {user.get('full_name', user.get('username', 'bạn'))} 👋
        </h1>
        <p style="color:#8b949e;font-size:14px;max-width:520px;margin:0 0 24px;line-height:1.6;">
            Hệ thống giám sát tài xế thời gian thực sử dụng <strong style="color:#e6edf3;">
            Deep Learning (MobileNetV2)</strong> kết hợp phân tích hình học khuôn mặt
            (EAR · MAR · Head Pose) để phát hiện buồn ngủ.
        </p>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
            {'<a style="background:#2f81f7;color:#fff;padding:8px 20px;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;cursor:pointer;" href="#">📊 Xem Dashboard</a>'
              if role == 'admin' else
              '<a style="background:#2f81f7;color:#fff;padding:8px 20px;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;" href="#">📷 Bắt đầu giám sát</a>'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row ───────────────────────────────────────────────
    kpi = get_kpi(days=30)

    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        st.markdown(kpi_card("Tài xế", kpi["drivers"],
                             "đang hoạt động", "accent", "👥"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Cảnh báo", kpi["alerts"],
                             "30 ngày qua", "warning", "🚨"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Ngủ gật", kpi["drowsy"],
                             "DROWSY phát hiện", "danger", "😴"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Ngáp", kpi["yawns"],
                             "lần ghi nhận", "success", "🥱"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Feature cards ─────────────────────────────────────────
    st.markdown("### Tính năng hệ thống")
    f1, f2, f3 = st.columns(3, gap="medium")
    features = [
        ("🧠", "Deep Learning", "MobileNetV2 transfer learning phân loại mắt và miệng với độ chính xác 92–97%."),
        ("📐", "Geometric Fusion", "EAR, MAR, Blink Rate và Head Pose kết hợp với CNN để tăng độ tin cậy."),
        ("⚡", "Real-time", "Pipeline 15–30 FPS với cảnh báo âm thanh tức thì khi phát hiện nguy hiểm."),
    ]
    for col, (icon, title, desc) in zip([f1, f2, f3], features):
        with col:
            st.markdown(f"""
            <div style="background:#1c2333;border:1px solid #30363d;border-radius:12px;
                        padding:24px;height:160px;">
                <div style="font-size:1.8rem;margin-bottom:10px;">{icon}</div>
                <div style="font-size:14px;font-weight:600;color:#e6edf3;margin-bottom:6px;">{title}</div>
                <div style="font-size:12px;color:#8b949e;line-height:1.6;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Quick actions ─────────────────────────────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("### Truy cập nhanh")
    q1, q2, q3 = st.columns(3, gap="small")

    if role == "admin":
        actions = [
            ("dashboard", "📊", "Dashboard", "Xem tổng quan & biểu đồ"),
            ("drivers",   "👥", "Tài xế",    "Quản lý danh sách tài xế"),
            ("alerts",    "🚨", "Vi phạm",   "Xem log cảnh báo chi tiết"),
        ]
    else:
        actions = [
            ("monitor",  "📷", "Giám sát",  "Bắt đầu phiên giám sát"),
            ("history",  "📋", "Lịch sử",   "Xem lịch sử cảnh báo"),
            ("profile",  "👤", "Hồ sơ",     "Cập nhật thông tin"),
        ]

    for col, (page, icon, title, desc) in zip([q1, q2, q3], actions):
        with col:
            if st.button(f"{icon}  {title}", use_container_width=True, key=f"qa_{page}"):
                st.session_state.page = page
                st.rerun()
            st.caption(desc)
