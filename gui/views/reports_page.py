# views/reports_page.py  –  Báo cáo theo ngày/tháng
import streamlit as st
import pandas as pd
from components.styles import inject_css, section_header, page_header, kpi_card
from components import charts
from database.db import (
    get_monthly_stats, get_alerts_timeseries,
    get_recent_alerts, get_all_users, get_kpi,
)


def render():
    inject_css()
    user = st.session_state.user
    role = user["role"]
    uid  = user["id"] if role == "driver" else None

    page_header("📈 Báo cáo", "Thống kê theo ngày và tháng")

    tabs = st.tabs(["📅  Theo ngày", "📆  Theo tháng", "📊  So sánh tài xế"])

    # ════════════════════════════════════════════════════════
    #  Tab 1 – Theo ngày
    # ════════════════════════════════════════════════════════
    with tabs[0]:
        section_header("Bộ lọc")
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            days = st.selectbox("Số ngày gần nhất", [7, 14, 30, 60, 90],
                                index=2, key="rp_days",
                                format_func=lambda x: f"{x} ngày")
        with fc2:
            if role == "admin":
                drivers = get_all_users(role="driver")
                opts = {"Tất cả": None}
                opts.update({d["full_name"]: d["id"] for d in drivers})
                sel  = st.selectbox("Tài xế", list(opts.keys()), key="rp_drv")
                uid_f = opts[sel]
            else:
                uid_f = uid
                st.info(f"Tài xế: **{user['full_name']}**")
        with fc3:
            status_f = st.selectbox("Trạng thái", ["Tất cả", "TIRED", "DROWSY"],
                                    key="rp_status")

        # KPI
        rows = get_recent_alerts(user_id=uid_f, limit=1000, days=days,
                                 status_filter=status_f)
        df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()

        k1, k2, k3, k4 = st.columns(4)
        total   = len(df)
        drowsy  = len(df[df.status == "DROWSY"]) if not df.empty else 0
        tired   = len(df[df.status == "TIRED"])  if not df.empty else 0
        avg_sc  = f"{df['score'].mean():.1f}" if not df.empty else "—"

        with k1: st.markdown(kpi_card("Tổng cảnh báo", total,   f"{days}d", "accent",  "🚨"), unsafe_allow_html=True)
        with k2: st.markdown(kpi_card("DROWSY",  drowsy, "lần", "danger",  "😴"), unsafe_allow_html=True)
        with k3: st.markdown(kpi_card("TIRED",   tired,  "lần", "warning", "⚠️"), unsafe_allow_html=True)
        with k4: st.markdown(kpi_card("Score TB", avg_sc, "",   "success", "📊"), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Charts
        ts_rows = get_alerts_timeseries(user_id=uid_f, days=days)
        col_ts, col_pie = st.columns([3, 2], gap="medium")
        with col_ts:
            st.plotly_chart(charts.alerts_timeseries(ts_rows),
                            use_container_width=True, config={"displayModeBar": False})
        with col_pie:
            st.plotly_chart(charts.status_donut(ts_rows),
                            use_container_width=True, config={"displayModeBar": False})

        # EAR/MAR scatter
        section_header("Phân tán EAR vs MAR")
        st.plotly_chart(charts.ear_mar_scatter(rows),
                        use_container_width=True, config={"displayModeBar": False})

        # Bảng chi tiết
        section_header("Chi tiết theo ngày")
        if not df.empty:
            daily = (
                df.assign(day=df["timestamp"].str[:10])
                  .groupby("day")
                  .agg(
                      total=("status", "count"),
                      drowsy=("status", lambda x: (x == "DROWSY").sum()),
                      tired=("status",  lambda x: (x == "TIRED").sum()),
                      avg_score=("score", "mean"),
                      min_score=("score", "min"),
                  )
                  .reset_index()
                  .sort_values("day", ascending=False)
            )
            daily.columns = ["Ngày", "Tổng", "DROWSY", "TIRED",
                             "Score TB", "Score thấp nhất"]
            daily["Score TB"]        = daily["Score TB"].round(1)
            daily["Score thấp nhất"] = daily["Score thấp nhất"].round(1)
            st.dataframe(daily, use_container_width=True, height=300)

            csv = daily.to_csv(index=False).encode()
            st.download_button("⬇️ Xuất CSV (ngày)", csv,
                               "report_daily.csv", "text/csv")
        else:
            st.info("Không có dữ liệu trong khoảng thời gian đã chọn.")

    # ════════════════════════════════════════════════════════
    #  Tab 2 – Theo tháng
    # ════════════════════════════════════════════════════════
    with tabs[1]:
        section_header("Báo cáo theo tháng")
        mc1, mc2 = st.columns(2)
        with mc1:
            months = st.selectbox("Số tháng", [3, 6, 12], index=1,
                                  key="rp_months",
                                  format_func=lambda x: f"{x} tháng")
        with mc2:
            if role == "admin":
                drivers2 = get_all_users(role="driver")
                opts2 = {"Tất cả": None}
                opts2.update({d["full_name"]: d["id"] for d in drivers2})
                sel2   = st.selectbox("Tài xế", list(opts2.keys()), key="rp_drv2")
                uid_f2 = opts2[sel2]
            else:
                uid_f2 = uid
                st.info(f"Tài xế: **{user['full_name']}**")

        monthly_rows = get_monthly_stats(user_id=uid_f2, months=months)

        st.plotly_chart(charts.monthly_trend(monthly_rows),
                        use_container_width=True, config={"displayModeBar": False})

        if monthly_rows:
            df_m = pd.DataFrame(
                [dict(r) for r in monthly_rows],
                columns=["Tháng", "Tổng cảnh báo", "DROWSY"],
            )
            df_m["TIRED"] = df_m["Tổng cảnh báo"] - df_m["DROWSY"]
            st.dataframe(df_m, use_container_width=True, height=260)

            csv_m = df_m.to_csv(index=False).encode()
            st.download_button("⬇️ Xuất CSV (tháng)", csv_m,
                               "report_monthly.csv", "text/csv")
        else:
            st.info("Chưa có dữ liệu.")

    # ════════════════════════════════════════════════════════
    #  Tab 3 – So sánh tài xế (chỉ Admin)
    # ════════════════════════════════════════════════════════
    with tabs[2]:
        if role != "admin":
            st.info("⛔ Chức năng này chỉ dành cho Admin.")
            return

        section_header("So sánh hiệu suất tài xế")
        cmp_days = st.selectbox("Khoảng TG", [7, 14, 30, 60], index=2,
                                key="rp_cmp_days",
                                format_func=lambda x: f"{x} ngày")

        from database.db import get_alerts_by_driver
        driver_rows = get_alerts_by_driver(days=cmp_days)

        if driver_rows:
            df_d = pd.DataFrame(
                [dict(r) for r in driver_rows],
                columns=["full_name", "username", "total",
                         "drowsy", "tired", "min_score"],
            )

            # Bar chart so sánh
            st.plotly_chart(charts.driver_bar(driver_rows),
                            use_container_width=True, config={"displayModeBar": False})

            # Bảng xếp hạng
            section_header("Xếp hạng tài xế (theo số cảnh báo)")
            df_rank = df_d.copy()
            df_rank.index = range(1, len(df_rank) + 1)
            df_rank.columns = ["Họ tên", "Username", "Tổng CÁO",
                               "DROWSY", "TIRED", "Score thấp nhất"]

            def highlight_risk(row):
                if row["DROWSY"] >= 5:
                    return ["background-color:#3a1a1a"] * len(row)
                elif row["DROWSY"] >= 2:
                    return ["background-color:#3a2e1a"] * len(row)
                return [""] * len(row)

            st.dataframe(
                df_rank.style.apply(highlight_risk, axis=1),
                use_container_width=True, height=320,
            )

            csv_d = df_rank.to_csv().encode()
            st.download_button("⬇️ Xuất CSV (tài xế)", csv_d,
                               "report_drivers.csv", "text/csv")
        else:
            st.info("Chưa có dữ liệu so sánh.")
