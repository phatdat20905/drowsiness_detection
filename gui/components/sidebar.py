# ============================================================
#  components/sidebar.py  –  Navigation sidebar
# ============================================================

import streamlit as st


def render_sidebar():
    user = st.session_state.get("user", {})
    role = user.get("role", "driver")

    with st.sidebar:
        # Logo + system name
        st.markdown("""
        <div style="padding:16px 0 20px;border-bottom:1px solid #30363d;margin-bottom:12px;">
            <div style="font-size:1.6rem;margin-bottom:4px;">🚗</div>
            <div style="font-size:14px;font-weight:700;color:#e6edf3;">Driver Monitoring</div>
            <div style="font-size:11px;color:#484f58;">System v2.0</div>
        </div>
        """, unsafe_allow_html=True)

        # User info
        st.markdown(f"""
        <div style="background:#1c2333;border:1px solid #30363d;border-radius:10px;
                    padding:12px 14px;margin-bottom:16px;">
            <div style="font-size:13px;font-weight:600;color:#e6edf3;margin-bottom:2px;">
                {user.get('full_name', user.get('username', ''))}
            </div>
            <div style="font-size:11px;color:#8b949e;">
                {'👑 Admin' if role == 'admin' else '🚘 Tài xế'}
                &nbsp;·&nbsp; @{user.get('username', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        current = st.session_state.get("page", "home")

        # Common views
        _nav_group("CHÍNH")
        _nav_btn("🏠", "Tổng quan",    "home",    current)

        if role == "admin":
            _nav_group("QUẢN LÝ")
            _nav_btn("📊", "Dashboard",    "dashboard", current)
            _nav_btn("👥", "Tài xế",       "drivers",   current)
            _nav_btn("🚨", "Vi phạm",      "alerts",    current)
            _nav_btn("📈", "Báo cáo",      "reports",   current)
        else:
            _nav_group("GIÁM SÁT")
            _nav_btn("📷", "Giám sát",     "monitor",   current)
            _nav_btn("📋", "Lịch sử",      "history",   current)
            _nav_btn("📈", "Báo cáo",      "reports",   current)

        _nav_group("TÀI KHOẢN")
        _nav_btn("👤", "Hồ sơ",         "profile",   current)

        # Logout
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown('<div style="border-top:1px solid #30363d;padding-top:12px;">', unsafe_allow_html=True)
        if st.button("⬅️  Đăng xuất", use_container_width=True):
            from components.auth import logout
            logout()
        st.markdown('</div>', unsafe_allow_html=True)


def _nav_group(label: str):
    st.markdown(f"""
    <div style="font-size:10px;font-weight:700;letter-spacing:.08em;
                color:#484f58;padding:12px 0 4px;text-transform:uppercase;">
        {label}
    </div>""", unsafe_allow_html=True)


def _nav_btn(icon: str, label: str, page_key: str, current: str):
    active = current == page_key
    style = (
        "background:rgba(47,129,247,0.12);color:#2f81f7;border:1px solid rgba(47,129,247,.25);"
        if active else
        "background:transparent;color:#8b949e;border:1px solid transparent;"
    )
    clicked = st.button(
        f"{icon}  {label}",
        key=f"nav_{page_key}",
        use_container_width=True,
    )
    if clicked:
        st.session_state.page = page_key
        st.rerun()
