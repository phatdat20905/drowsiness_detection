# ============================================================
#  components/auth.py  –  Login / session helpers
# ============================================================

import streamlit as st
from database.db import authenticate


def require_login():
    """
    Kiểm tra session. Nếu chưa login → hiện form login + stop.
    Trả về dict user nếu đã login.
    """
    if "user" not in st.session_state or st.session_state.user is None:
        _render_login()
        st.stop()
    return st.session_state.user


def require_admin():
    user = require_login()
    if user["role"] != "admin":
        st.error("⛔ Bạn không có quyền truy cập trang này.")
        st.stop()
    return user


def logout():
    st.session_state.clear()
    st.rerun()


def _render_login():
    from components.styles import inject_css
    inject_css()

    # Centered login card
    st.markdown("""
    <div style="max-width:420px;margin:80px auto 0;padding:0 1rem;">
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:2.8rem;margin-bottom:8px;">🚗</div>
            <h1 style="font-size:22px;font-weight:700;color:#e6edf3;margin:0;">
                Driver Monitoring System
            </h1>
            <p style="color:#8b949e;font-size:13px;margin-top:6px;">
                Đăng nhập để tiếp tục
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        with st.form("login_form"):
            st.markdown('<div style="margin-bottom:4px;font-size:13px;color:#8b949e;">Tên đăng nhập</div>',
                        unsafe_allow_html=True)
            username = st.text_input("", placeholder="username", label_visibility="collapsed")

            st.markdown('<div style="margin-bottom:4px;font-size:13px;color:#8b949e;">Mật khẩu</div>',
                        unsafe_allow_html=True)
            password = st.text_input("", type="password", placeholder="••••••••",
                                     label_visibility="collapsed")

            submitted = st.form_submit_button("Đăng nhập", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("Vui lòng nhập đầy đủ thông tin.")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = dict(user)
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("Tên đăng nhập hoặc mật khẩu không đúng.")

        st.markdown("""
        <div style="text-align:center;margin-top:16px;font-size:12px;color:#484f58;">
            Demo: <code>admin / admin123</code> &nbsp;|&nbsp;
            <code>driver1 / driver123</code>
        </div>""", unsafe_allow_html=True)
