# views/alerts_page.py  –  Vi phạm (Admin)
import streamlit as st
import pandas as pd
from components.styles import inject_css, section_header, page_header
from components import charts
from database.db import get_recent_alerts, get_all_users, get_alerts_timeseries


def render():
    inject_css()
    page_header("🚨 Quản lý vi phạm", "Log cảnh báo TIRED / DROWSY toàn hệ thống")

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        days = st.selectbox("Khoảng TG", [1, 7, 14, 30, 60], index=1,
                            format_func=lambda x: f"{x} ngày")
    with col2:
        drivers = get_all_users(role="driver")
        opts = {"Tất cả": None}
        opts.update({f"{d['full_name']}": d["id"] for d in drivers})
        d_sel = st.selectbox("Tài xế", list(opts.keys()))
        uid   = opts[d_sel]
    with col3:
        status_f = st.selectbox("Trạng thái", ["Tất cả", "TIRED", "DROWSY"])
    with col4:
        limit = st.selectbox("Số hàng", [50, 100, 200, 500], index=0)

    rows = get_recent_alerts(user_id=uid, limit=limit, days=days,
                             status_filter=status_f)

    # Summary row
    if rows:
        df_all = pd.DataFrame([dict(r) for r in rows])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng cảnh báo", len(df_all))
        m2.metric("DROWSY", len(df_all[df_all.status == "DROWSY"]))
        m3.metric("TIRED",  len(df_all[df_all.status == "TIRED"]))
        m4.metric("Score TB", f"{df_all['score'].mean():.1f}")

    # Charts
    section_header("Phân bố theo thời gian")
    ts_rows = get_alerts_timeseries(user_id=uid, days=days)
    c1, c2 = st.columns([3, 2])
    with c1:
        st.plotly_chart(charts.alerts_timeseries(ts_rows),
                        use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.plotly_chart(charts.status_donut(ts_rows),
                        use_container_width=True, config={"displayModeBar": False})

    # EAR/MAR scatter
    section_header("Phân tán EAR vs MAR")
    st.plotly_chart(charts.ear_mar_scatter(rows),
                    use_container_width=True, config={"displayModeBar": False})

    # Table
    section_header("Chi tiết vi phạm")
    if rows:
        show_cols = ["timestamp", "full_name", "status", "score",
                     "ear", "mar", "blink_rate", "head_pose",
                     "cnn_prob_eye", "cnn_prob_mouth"]
        df_show = pd.DataFrame([dict(r) for r in rows])[show_cols]
        df_show.columns = ["Thời gian", "Tài xế", "Trạng thái", "Score",
                           "EAR", "MAR", "Blink", "Pose", "CNN Eye", "CNN Mouth"]
        df_show["Trạng thái"] = df_show["Trạng thái"].map({
            "TIRED": "⚠️ TIRED", "DROWSY": "🚨 DROWSY"
        })
        st.dataframe(df_show, use_container_width=True, height=380)

        csv = df_show.to_csv(index=False).encode()
        st.download_button("⬇️ Xuất CSV", csv, "violations.csv", "text/csv")
    else:
        st.info("Không có vi phạm nào trong bộ lọc đã chọn.")
