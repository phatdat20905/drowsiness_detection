# ============================================================
#  app.py  –  Entry point duy nhất
#  Chạy: streamlit run gui/app.py
# ============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# ── Page config (phải gọi TRƯỚC mọi st.xxx khác) ─────────────
st.set_page_config(
    page_title="Driver Monitoring",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Init DB ───────────────────────────────────────────────────
from database.db import init_db
init_db()

# ── Auth gate ─────────────────────────────────────────────────
from components.auth import require_login
user = require_login()        # redirect → login form nếu chưa login

# ── Sidebar navigation ────────────────────────────────────────
from components.sidebar import render_sidebar
from components.styles  import inject_css
inject_css()
render_sidebar()

# ── Router ────────────────────────────────────────────────────
page = st.session_state.get("page", "home")
role = user.get("role", "driver")

# Bảo vệ trang admin
ADMIN_ONLY = {"dashboard", "drivers", "alerts"}
if page in ADMIN_ONLY and role != "admin":
    st.session_state.page = "home"
    page = "home"

# Driver không có trang monitor → chuyển về home
DRIVER_ONLY = {"monitor", "history"}
if page in DRIVER_ONLY and role == "admin":
    # Admin vẫn có thể xem nhưng chỉ hiện thông báo
    pass

# ── Render page ───────────────────────────────────────────────
if page == "home":
    from views.home_page import render
    render()

elif page == "dashboard":
    if role == "admin":
        from views.dashboard_page import render
        render()
    else:
        st.error("⛔ Không có quyền truy cập.")

elif page == "drivers":
    if role == "admin":
        from views.drivers_page import render
        render()
    else:
        st.error("⛔ Không có quyền truy cập.")

elif page == "alerts":
    if role == "admin":
        from views.alerts_page import render
        render()
    else:
        st.error("⛔ Không có quyền truy cập.")

elif page == "monitor":
    from views.monitor_page import render
    render()

elif page == "history":
    from views.history_page import render
    render()

elif page == "reports":
    from views.reports_page import render
    render()

elif page == "profile":
    from views.profile_page import render
    render()

else:
    st.session_state.page = "home"
    st.rerun()
