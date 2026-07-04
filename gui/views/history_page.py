# views/history_page.py  –  Lịch sử cá nhân (Driver)
import streamlit as st
import pandas as pd
from components.styles import inject_css, section_header, page_header
from components import charts
from database.db import get_recent_alerts, get_alerts_timeseries, get_kpi


def render():
    inject_css()
    user = st.session_state.user
    uid  = user["id"]

    page_header("📋 Lịch sử cảnh báo", f"Tài xế: {user['full_name']}")

    col_d, col_s = st.columns([2, 2])
    with col_d:
        days = st.selectbox("Khoảng TG", [7, 14, 30, 60], index=0,
                            format_func=lambda x: f"{x} ngày")
    with col_s:
        status_f = st.selectbox("Trạng thái", ["Tất cả", "TIRED", "DROWSY"])

    # KPI personal
    rows = get_recent_alerts(user_id=uid, limit=500, days=days, status_filter=status_f)
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cảnh báo", len(df))
    m2.metric("DROWSY", len(df[df.status == "DROWSY"]) if not df.empty else 0)
    m3.metric("TIRED",  len(df[df.status == "TIRED"])  if not df.empty else 0)
    m4.metric("Score TB",
              f"{df['score'].mean():.1f}" if not df.empty else "—")

    # Charts
    section_header("Xu hướng cảnh báo")
    ts_rows = get_alerts_timeseries(user_id=uid, days=days)
    c1, c2 = st.columns([3, 2])
    with c1:
        st.plotly_chart(charts.alerts_timeseries(ts_rows),
                        use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.plotly_chart(charts.status_donut(ts_rows),
                        use_container_width=True, config={"displayModeBar": False})

    # Table
    section_header("Chi tiết")
    if not df.empty:
        show = df[["timestamp", "status", "score", "ear", "mar",
                   "blink_rate", "head_pose"]].copy()
        show.columns = ["Thời gian", "Trạng thái", "Score",
                        "EAR", "MAR", "Blink/min", "Head Pose"]
        show["Trạng thái"] = show["Trạng thái"].map({
            "TIRED": "⚠️ TIRED", "DROWSY": "🚨 DROWSY", "NORMAL": "✅ NORMAL"
        })
        st.dataframe(show, use_container_width=True, height=340)
        csv = show.to_csv(index=False).encode()
        st.download_button("⬇️ Xuất CSV", csv, "my_alerts.csv", "text/csv")
    else:
        st.info("Không có cảnh báo nào trong khoảng thời gian đã chọn. 🎉")
