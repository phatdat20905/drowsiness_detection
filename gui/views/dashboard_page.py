# views/dashboard_page.py  –  Admin analytics dashboard
import streamlit as st
import pandas as pd

from components.styles import inject_css, kpi_card, section_header, page_header
from components import charts
from database.db import (
    get_kpi, get_alerts_timeseries, get_alerts_by_driver,
    get_monthly_stats, get_recent_alerts, get_all_users,
)


def render():
    inject_css()
    page_header("📊 Dashboard", "Tổng quan hệ thống giám sát tài xế")

    # ── Filters ───────────────────────────────────────────────
    with st.expander("🔍 Bộ lọc", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            days = st.selectbox("Khoảng thời gian", [7, 14, 30, 60, 90],
                                index=2, format_func=lambda x: f"{x} ngày")
        with fc2:
            drivers = get_all_users(role="driver")
            driver_opts = {"Tất cả": None}
            driver_opts.update({f"{d['full_name']} (@{d['username']})": d["id"]
                                for d in drivers})
            driver_sel = st.selectbox("Tài xế", list(driver_opts.keys()))
            selected_uid = driver_opts[driver_sel]
        with fc3:
            status_sel = st.selectbox("Trạng thái", ["Tất cả", "TIRED", "DROWSY"])

    # ── KPI Cards ─────────────────────────────────────────────
    kpi = get_kpi(days=days)
    k1, k2, k3, k4, k5 = st.columns(5, gap="small")
    cards = [
        (k1, "Tài xế", kpi["drivers"],     "đang hoạt động",   "accent",  "👥"),
        (k2, "Cảnh báo", kpi["alerts"],    f"{days}d qua",      "warning", "🚨"),
        (k3, "DROWSY",   kpi["drowsy"],    "nguy hiểm",         "danger",  "😴"),
        (k4, "Nhắm mắt", kpi["closed_eyes"], "tổng lần",       "accent",  "👁️"),
        (k5, "Ngáp",    kpi["yawns"],      "tổng lần",          "success", "🥱"),
    ]
    for col, label, value, delta, variant, icon in cards:
        with col:
            st.markdown(kpi_card(label, f"{value:,}", delta, variant, icon),
                        unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Row 1: Timeseries + Donut ──────────────────────────────
    section_header("Phân tích cảnh báo")
    col_ts, col_donut = st.columns([3, 2], gap="medium")

    ts_rows = get_alerts_timeseries(user_id=selected_uid, days=days)
    with col_ts:
        st.plotly_chart(charts.alerts_timeseries(ts_rows),
                        use_container_width=True, config={"displayModeBar": False})
    with col_donut:
        st.plotly_chart(charts.status_donut(ts_rows),
                        use_container_width=True, config={"displayModeBar": False})

    # ── Row 2: Driver bar + Monthly trend ─────────────────────
    col_bar, col_trend = st.columns([3, 2], gap="medium")
    driver_rows = get_alerts_by_driver(days=days)
    monthly_rows = get_monthly_stats(user_id=selected_uid, months=6)

    with col_bar:
        st.plotly_chart(charts.driver_bar(driver_rows),
                        use_container_width=True, config={"displayModeBar": False})
    with col_trend:
        st.plotly_chart(charts.monthly_trend(monthly_rows),
                        use_container_width=True, config={"displayModeBar": False})

    # ── Row 3: EAR/MAR scatter ────────────────────────────────
    section_header("Phân tích chỉ số sinh trắc học")
    alert_rows = get_recent_alerts(user_id=selected_uid, days=days,
                                   limit=500, status_filter=status_sel)
    col_scatter, col_table = st.columns([3, 2], gap="medium")
    with col_scatter:
        st.plotly_chart(charts.ear_mar_scatter(alert_rows),
                        use_container_width=True, config={"displayModeBar": False})

    with col_table:
        section_header("Tài xế nguy cơ cao")
        if driver_rows:
            df_d = pd.DataFrame(
                [dict(r) for r in driver_rows],
                columns=["full_name", "username", "total", "drowsy", "tired", "min_score"]
            ).head(8)
            df_d.columns = ["Tên", "Username", "Tổng", "DROWSY", "TIRED", "Score thấp"]
            st.dataframe(df_d, use_container_width=True, height=260)
        else:
            st.info("Chưa có dữ liệu.")

    # ── Recent alerts table ───────────────────────────────────
    section_header("Vi phạm gần nhất")
    if alert_rows:
        cols_show = ["timestamp", "full_name", "status", "score",
                     "ear", "mar", "blink_rate", "head_pose"]
        df_a = pd.DataFrame([dict(r) for r in alert_rows[:50]])[cols_show]
        df_a.columns = ["Thời gian", "Tài xế", "Trạng thái", "Score",
                        "EAR", "MAR", "Blink/min", "Head Pose"]
        df_a["Trạng thái"] = df_a["Trạng thái"].map({
            "TIRED": "⚠️ TIRED", "DROWSY": "🚨 DROWSY", "NORMAL": "✅ NORMAL"
        })
        st.dataframe(df_a, use_container_width=True, height=280)

        # Download
        csv = df_a.to_csv(index=False).encode()
        st.download_button("⬇️ Tải CSV", csv, "alerts_export.csv",
                           "text/csv", use_container_width=False)
    else:
        st.info("Không có vi phạm trong khoảng thời gian đã chọn.")
